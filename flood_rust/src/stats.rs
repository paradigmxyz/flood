use chrono::{DateTime, Local};
use std::cmp::min;
use std::collections::HashSet;
use std::num::NonZeroUsize;
use std::time::{Instant, SystemTime};

use cpu_time::ProcessTime;
use hdrhistogram::Histogram;
use serde::{Deserialize, Serialize};
use statrs::distribution::{ContinuousCDF, StudentsT};
use strum::EnumCount;
use strum::IntoEnumIterator;
use strum_macros::{EnumCount as EnumCountM, EnumIter};

use crate::histogram::SerializableHistogram;
use crate::workload::WorkloadStats;

/// Controls the maximum order of autocovariance taken into
/// account when estimating the long run mean error. Higher values make the estimator
/// capture more autocorrelation from the signal, but also make the results
/// more random. Lower values increase the bias (underestimation) of error, but offer smoother
/// results for small N and better performance for large N.
/// The value has been established empirically.
/// Probably anything between 0.2 and 0.8 is good enough.
/// Valid range is 0.0 to 1.0.
const BANDWIDTH_COEFF: f64 = 0.5;

/// Arithmetic weighted mean of values in the vector
pub fn mean(values: &[f32], weights: &[f32]) -> f64 {
    let sum_values = values
        .iter()
        .zip(weights)
        .map(|(&v, &w)| (v as f64) * (w as f64))
        .sum::<f64>();
    let sum_weights = weights.iter().map(|&v| v as f64).sum::<f64>();
    sum_values / sum_weights
}

/// Estimates the variance of the mean of a time-series.
/// Takes into account the fact that the observations can be dependent on each other
/// (i.e. there is a non-zero amount of auto-correlation in the signal).
///
/// Contrary to the classic variance estimator, the order of the
/// data points does matter here. If the observations are totally independent from each other,
/// the expected return value of this function is close to the expected sample variance.
pub fn long_run_variance(mean: f64, values: &[f32], weights: &[f32]) -> f64 {
    if values.len() <= 1 {
        return f64::NAN;
    }
    let len = values.len() as f64;

    // Compute the variance:
    let mut sum_weights = 0.0;
    let mut var = 0.0;
    for (&v, &w) in values.iter().zip(weights) {
        let diff = v as f64 - mean;
        let w = w as f64;
        var += diff * diff * w;
        sum_weights += w;
    }
    var /= sum_weights;

    // Compute a sum of autocovariances of orders 1 to (cutoff - 1).
    // Cutoff (bandwidth) and diminishing weights are needed to reduce random error
    // introduced by higher order autocovariance estimates.
    let bandwidth = len.powf(BANDWIDTH_COEFF);
    let max_lag = min(values.len(), bandwidth.ceil() as usize);
    let mut cov_sum = 0.0;
    for lag in 1..max_lag {
        let weight = 1.0 - lag as f64 / values.len() as f64;
        let mut cov = 0.0;
        let mut sum_weights = 0.0;
        for i in lag..values.len() {
            let diff_1 = values[i] as f64 - mean;
            let diff_2 = values[i - lag] as f64 - mean;
            let w = weights[i] as f64 * weights[i - lag] as f64;
            sum_weights += w;
            cov += 2.0 * diff_1 * diff_2 * weight * w;
        }
        cov_sum += cov / sum_weights;
    }

    // It is possible that we end up with a negative sum of autocovariances here.
    // But we don't want that because we're trying to estimate
    // the worst-case error and for small N this situation is likely a random coincidence.
    // Additionally, `var + cov` must be at least 0.0.
    cov_sum = cov_sum.max(0.0);

    // Correct bias for small n:
    let inflation = 1.0 + cov_sum / (var + f64::MIN_POSITIVE);
    let bias_correction = (inflation / len).exp();
    bias_correction * (var + cov_sum)
}

/// Estimates the error of the mean of a time-series.
/// See `long_run_variance`.
pub fn long_run_err(mean: f64, values: &[f32], weights: &[f32]) -> f64 {
    (long_run_variance(mean, values, weights) / values.len() as f64).sqrt()
}

fn percentiles_ms(hist: &Histogram<u64>) -> [f32; Percentile::COUNT] {
    let mut percentiles = [0.0; Percentile::COUNT];
    for (i, p) in Percentile::iter().enumerate() {
        percentiles[i] = hist.value_at_percentile(p.value()) as f32 / 1000000.0;
    }
    percentiles
}

/// Holds a mean and its error together.
/// Makes it more convenient to compare means and it also reduces the number
/// of fields, because we don't have to keep the values and the errors in separate fields.
#[derive(Debug, Copy, Clone, Serialize, Deserialize)]
pub struct Mean {
    pub n: u64,
    pub value: f64,
    pub std_err: Option<f64>,
}

impl Mean {
    pub fn compute(v: &[f32], weights: &[f32]) -> Self {
        let m = mean(v, weights);
        Mean {
            n: v.len() as u64,
            value: m,
            std_err: not_nan(long_run_err(m, v, weights)),
        }
    }
}

/// Returns the probability that the difference between two means is due to a chance.
/// Uses Welch's t-test allowing samples to have different variances.
/// See https://en.wikipedia.org/wiki/Welch%27s_t-test.
///
/// If any of the means is given without the error, or if the number of observations is too low,
/// returns 1.0.
///
/// Assumes data are i.i.d and distributed normally, but it can be used
/// for autocorrelated data as well, if the errors are properly corrected for autocorrelation
/// using Wilk's method. This is what `Mean` struct is doing automatically
/// when constructed from a vector.
pub fn t_test(mean1: &Mean, mean2: &Mean) -> f64 {
    if mean1.std_err.is_none() || mean2.std_err.is_none() {
        return 1.0;
    }
    let n1 = mean1.n as f64;
    let n2 = mean2.n as f64;
    let e1 = mean1.std_err.unwrap();
    let e2 = mean2.std_err.unwrap();
    let m1 = mean1.value;
    let m2 = mean2.value;
    let e1_sq = e1 * e1;
    let e2_sq = e2 * e2;
    let se_sq = e1_sq + e2_sq;
    let se = se_sq.sqrt();
    let t = (m1 - m2) / se;
    let freedom = se_sq * se_sq / (e1_sq * e1_sq / (n1 - 1.0) + e2_sq * e2_sq / (n2 - 1.0));
    if let Ok(distrib) = StudentsT::new(0.0, 1.0, freedom) {
        2.0 * (1.0 - distrib.cdf(t.abs()))
    } else {
        1.0
    }
}

fn distribution(hist: &Histogram<u64>) -> Vec<Bucket> {
    let mut result = Vec::new();
    if !hist.is_empty() {
        for x in hist.iter_log(100000, 2.15443469) {
            result.push(Bucket {
                percentile: x.percentile(),
                duration_ms: x.value_iterated_to() as f64 / 1000000.0,
                count: x.count_since_last_iteration(),
                cumulative_count: x.count_at_value(),
            });
        }
    }
    result
}

/// Converts NaN to None.
fn not_nan(x: f64) -> Option<f64> {
    if x.is_nan() {
        None
    } else {
        Some(x)
    }
}

/// Converts NaN to None.
fn not_nan_f32(x: f32) -> Option<f32> {
    if x.is_nan() {
        None
    } else {
        Some(x)
    }
}

const MAX_KEPT_ERRORS: usize = 10;

#[allow(non_camel_case_types)]
#[derive(Copy, Clone, EnumIter, EnumCountM)]
pub enum Percentile {
    Min = 0,
    P1,
    P2,
    P5,
    P10,
    P25,
    P50,
    P75,
    P90,
    P95,
    P98,
    P99,
    P99_9,
    P99_99,
    Max,
}

impl Percentile {
    pub fn value(&self) -> f64 {
        match self {
            Percentile::Min => 0.0,
            Percentile::P1 => 1.0,
            Percentile::P2 => 2.0,
            Percentile::P5 => 5.0,
            Percentile::P10 => 10.0,
            Percentile::P25 => 25.0,
            Percentile::P50 => 50.0,
            Percentile::P75 => 75.0,
            Percentile::P90 => 90.0,
            Percentile::P95 => 95.0,
            Percentile::P98 => 98.0,
            Percentile::P99 => 99.0,
            Percentile::P99_9 => 99.9,
            Percentile::P99_99 => 99.99,
            Percentile::Max => 100.0,
        }
    }

    pub fn name(&self) -> &'static str {
        match self {
            Percentile::Min => "  Min   ",
            Percentile::P1 => "    1   ",
            Percentile::P2 => "    2   ",
            Percentile::P5 => "    5   ",
            Percentile::P10 => "   10   ",
            Percentile::P25 => "   25   ",
            Percentile::P50 => "   50   ",
            Percentile::P75 => "   75   ",
            Percentile::P90 => "   90   ",
            Percentile::P95 => "   95   ",
            Percentile::P98 => "   98   ",
            Percentile::P99 => "   99   ",
            Percentile::P99_9 => "   99.9 ",
            Percentile::P99_99 => "  99.99",
            Percentile::Max => "  Max   ",
        }
    }
}

/// Records basic statistics for a sample (a group) of requests
#[derive(Serialize, Deserialize)]
pub struct Sample {
    pub time_s: f32,
    pub duration_s: f32,
    pub cycle_count: u64,
    pub request_count: u64,
    pub error_count: u64,
    pub errors: HashSet<String>,
    pub mean_queue_len: f32,
    pub cycle_throughput: f32,
    pub req_throughput: f32,
    pub mean_cycle_time_ms: f32,
    pub mean_resp_time_ms: f32,
    pub cycle_time_percentiles: [f32; Percentile::COUNT],
    pub resp_time_percentiles: [f32; Percentile::COUNT],
    pub cycle_time_histogram_ns: SerializableHistogram,
    pub resp_time_histogram_ns: SerializableHistogram,
}

impl Sample {
    pub fn new(base_start_time: Instant, stats: &[WorkloadStats]) -> Sample {
        assert!(!stats.is_empty());
        let mut cycle_count = 0;
        let mut cycle_times_ns = Histogram::new(3).unwrap();

        let mut request_count = 0;
        let mut errors = HashSet::new();
        let mut error_count = 0;
        let mut mean_queue_len = 0.0;
        let mut duration_s = 0.0;
        let mut resp_times_ns = Histogram::new(3).unwrap();

        let mut cycle_time_histogram_ns = Histogram::new(3).unwrap();
        let mut resp_time_histogram_ns = Histogram::new(3).unwrap();

        for s in stats {
            let ss = &s.session_stats;
            let fs = &s.workload_stats;
            request_count += ss.req_count;
            if errors.len() < MAX_KEPT_ERRORS {
                errors.extend(ss.req_errors.iter().cloned());
            }
            error_count += ss.req_error_count;
            mean_queue_len += ss.mean_queue_length / stats.len() as f32;
            duration_s += (s.end_time - s.start_time).as_secs_f32() / stats.len() as f32;
            resp_times_ns.add(&ss.resp_times_ns).unwrap();
            resp_time_histogram_ns.add(&ss.resp_times_ns).unwrap();

            cycle_count += fs.workload_count;
            cycle_times_ns.add(&fs.workload_times_ns).unwrap();
            cycle_time_histogram_ns.add(&fs.workload_times_ns).unwrap();
        }
        let resp_time_percentiles = percentiles_ms(&resp_times_ns);
        let call_time_percentiles = percentiles_ms(&cycle_times_ns);

        Sample {
            time_s: (stats[0].start_time - base_start_time).as_secs_f32(),
            duration_s,
            cycle_count,
            request_count,
            error_count,
            errors,
            mean_queue_len: not_nan_f32(mean_queue_len).unwrap_or(0.0),
            cycle_throughput: cycle_count as f32 / duration_s,
            req_throughput: request_count as f32 / duration_s,
            mean_cycle_time_ms: cycle_times_ns.mean() as f32 / 1000000.0,
            cycle_time_histogram_ns: SerializableHistogram(cycle_time_histogram_ns),
            cycle_time_percentiles: call_time_percentiles,
            mean_resp_time_ms: resp_times_ns.mean() as f32 / 1000000.0,
            resp_time_percentiles,
            resp_time_histogram_ns: SerializableHistogram(resp_time_histogram_ns),
        }
    }
}

/// Collects the samples and computes aggregate statistics
struct Log {
    samples: Vec<Sample>,
}

impl Log {
    fn new() -> Log {
        Log {
            samples: Vec::new(),
        }
    }

    fn append(&mut self, sample: Sample) -> &Sample {
        self.samples.push(sample);
        self.samples.last().unwrap()
    }

    fn weights_by_call_count(&self) -> Vec<f32> {
        self.samples.iter().map(|s| s.cycle_count as f32).collect()
    }

    fn weights_by_request_count(&self) -> Vec<f32> {
        self.samples
            .iter()
            .map(|s| s.request_count as f32)
            .collect()
    }

    fn call_throughput(&self) -> Mean {
        let t: Vec<f32> = self.samples.iter().map(|s| s.cycle_throughput).collect();
        let w: Vec<f32> = self.samples.iter().map(|s| s.duration_s).collect();
        Mean::compute(t.as_slice(), w.as_slice())
    }

    fn req_throughput(&self) -> Mean {
        let t: Vec<f32> = self.samples.iter().map(|s| s.req_throughput).collect();
        let w: Vec<f32> = self.samples.iter().map(|s| s.duration_s).collect();
        Mean::compute(t.as_slice(), w.as_slice())
    }

    fn resp_time_ms(&self) -> Mean {
        let t: Vec<f32> = self.samples.iter().map(|s| s.mean_resp_time_ms).collect();
        let w = self.weights_by_request_count();
        Mean::compute(t.as_slice(), w.as_slice())
    }

    fn resp_time_percentile(&self, p: Percentile) -> Mean {
        let t: Vec<f32> = self
            .samples
            .iter()
            .map(|s| s.resp_time_percentiles[p as usize])
            .collect();
        let w = self.weights_by_request_count();
        Mean::compute(t.as_slice(), w.as_slice())
    }

    fn cycle_time_ms(&self) -> Mean {
        let t: Vec<f32> = self.samples.iter().map(|s| s.mean_cycle_time_ms).collect();
        let w = self.weights_by_call_count();
        Mean::compute(t.as_slice(), w.as_slice())
    }

    fn cycle_time_percentile(&self, p: Percentile) -> Mean {
        let t: Vec<f32> = self
            .samples
            .iter()
            .map(|s| s.cycle_time_percentiles[p as usize])
            .collect();
        let w = self.weights_by_call_count();
        Mean::compute(t.as_slice(), w.as_slice())
    }

    fn mean_concurrency(&self) -> Mean {
        let p: Vec<f32> = self.samples.iter().map(|s| s.mean_queue_len).collect();
        let w = self.weights_by_request_count();
        let m = Mean::compute(p.as_slice(), w.as_slice());
        if m.value.is_nan() {
            Mean {
                n: 0,
                value: 0.0,
                std_err: None,
            }
        } else {
            m
        }
    }
}

#[derive(Serialize, Deserialize)]
pub struct Bucket {
    pub percentile: f64,
    pub duration_ms: f64,
    pub count: u64,
    pub cumulative_count: u64,
}

#[derive(Serialize, Deserialize)]
pub struct TimeDistribution {
    pub mean: Mean,
    pub percentiles: Vec<Mean>,
    pub distribution: Vec<Bucket>,
}

/// Stores the final statistics of the test run.
#[derive(Serialize, Deserialize)]
pub struct BenchmarkStats {
    pub start_time: DateTime<Local>,
    pub end_time: DateTime<Local>,
    pub elapsed_time_s: f64,
    pub cpu_time_s: f64,
    pub cpu_util: f64,
    pub cycle_count: u64,
    pub request_count: u64,
    pub requests_per_cycle: f64,
    pub errors: Vec<String>,
    pub error_count: u64,
    pub errors_ratio: Option<f64>,
    pub cycle_throughput: Mean,
    pub cycle_throughput_ratio: Option<f64>,
    pub req_throughput: Mean,
    pub cycle_time_ms: TimeDistribution,
    pub resp_time_ms: Option<TimeDistribution>,
    pub concurrency: Mean,
    pub concurrency_ratio: f64,
    pub log: Vec<Sample>,
}

/// Stores the statistics of one or two test runs.
/// If the second run is given, enables comparisons between the runs.
pub struct BenchmarkCmp<'a> {
    pub v1: &'a BenchmarkStats,
    pub v2: Option<&'a BenchmarkStats>,
}

/// Significance level denoting strength of hypothesis.
/// The wrapped value denotes the probability of observing given outcome assuming
/// null-hypothesis is true (see: https://en.wikipedia.org/wiki/P-value).
#[derive(Clone, Copy)]
pub struct Significance(pub f64);

impl BenchmarkCmp<'_> {
    /// Compares samples collected in both runs for statistically significant difference.
    /// `f` a function applied to each sample
    fn cmp<F>(&self, f: F) -> Option<Significance>
    where
        F: Fn(&BenchmarkStats) -> Option<Mean> + Copy,
    {
        self.v2.and_then(|v2| {
            let m1 = f(self.v1);
            let m2 = f(v2);
            m1.and_then(|m1| m2.map(|m2| Significance(t_test(&m1, &m2))))
        })
    }

    /// Checks if call throughput means of two benchmark runs are significantly different.
    /// Returns None if the second benchmark is unset.
    pub fn cmp_cycle_throughput(&self) -> Option<Significance> {
        self.cmp(|s| Some(s.cycle_throughput))
    }

    /// Checks if request throughput means of two benchmark runs are significantly different.
    /// Returns None if the second benchmark is unset.
    pub fn cmp_req_throughput(&self) -> Option<Significance> {
        self.cmp(|s| Some(s.req_throughput))
    }

    // Checks if mean response time of two benchmark runs are significantly different.
    // Returns None if the second benchmark is unset.
    pub fn cmp_mean_resp_time(&self) -> Option<Significance> {
        self.cmp(|s| s.resp_time_ms.as_ref().map(|r| r.mean))
    }

    // Checks corresponding response time percentiles of two benchmark runs
    // are statistically different. Returns None if the second benchmark is unset.
    pub fn cmp_resp_time_percentile(&self, p: Percentile) -> Option<Significance> {
        self.cmp(|s| s.resp_time_ms.as_ref().map(|r| r.percentiles[p as usize]))
    }
}

/// Observes requests and computes their statistics such as mean throughput, mean response time,
/// throughput and response time distributions. Computes confidence intervals.
/// Can be also used to split the time-series into smaller sub-samples and to
/// compute statistics for each sub-sample separately.
pub struct Recorder {
    pub start_time: SystemTime,
    pub end_time: SystemTime,
    pub start_instant: Instant,
    pub end_instant: Instant,
    pub start_cpu_time: ProcessTime,
    pub end_cpu_time: ProcessTime,
    pub cycle_count: u64,
    pub request_count: u64,
    pub errors: HashSet<String>,
    pub error_count: u64,
    pub row_count: u64,
    pub cycle_times_ns: Histogram<u64>,
    pub resp_times_ns: Histogram<u64>,
    pub queue_len_sum: u64,
    log: Log,
    rate_limit: Option<f64>,
    concurrency_limit: NonZeroUsize,
}

impl Recorder {
    /// Creates a new recorder.
    /// The `rate_limit` and `concurrency_limit` parameters are used only as the
    /// reference levels for relative throughput and relative parallelism.
    pub fn start(rate_limit: Option<f64>, concurrency_limit: NonZeroUsize) -> Recorder {
        let start_time = SystemTime::now();
        let start_instant = Instant::now();
        Recorder {
            start_time,
            end_time: start_time,
            start_instant,
            end_instant: start_instant,
            start_cpu_time: ProcessTime::now(),
            end_cpu_time: ProcessTime::now(),
            log: Log::new(),
            rate_limit,
            concurrency_limit,
            cycle_count: 0,
            request_count: 0,
            row_count: 0,
            errors: HashSet::new(),
            error_count: 0,
            cycle_times_ns: Histogram::new(3).unwrap(),
            resp_times_ns: Histogram::new(3).unwrap(),
            queue_len_sum: 0,
        }
    }

    /// Adds the statistics of the completed request to the already collected statistics.
    /// Called on completion of each sample.
    pub fn record(&mut self, samples: &[WorkloadStats]) -> &Sample {
        for s in samples.iter() {
            self.resp_times_ns
                .add(&s.session_stats.resp_times_ns)
                .unwrap();
            self.cycle_times_ns
                .add(&s.workload_stats.workload_times_ns)
                .unwrap();
        }
        let stats = Sample::new(self.start_instant, samples);
        self.cycle_count += stats.cycle_count;
        self.request_count += stats.request_count;
        if self.errors.len() < MAX_KEPT_ERRORS {
            self.errors.extend(stats.errors.iter().cloned());
        }
        self.error_count += stats.error_count;
        self.log.append(stats)
    }

    /// Stops the recording, computes the statistics and returns them as the new object.
    pub fn finish(mut self) -> BenchmarkStats {
        self.end_time = SystemTime::now();
        self.end_instant = Instant::now();
        self.end_cpu_time = ProcessTime::now();
        self.stats()
    }

    /// Computes the final statistics based on collected data
    /// and turn them into report that can be serialized
    fn stats(self) -> BenchmarkStats {
        let elapsed_time_s = (self.end_instant - self.start_instant).as_secs_f64();
        let cpu_time_s = self
            .end_cpu_time
            .duration_since(self.start_cpu_time)
            .as_secs_f64();
        let cpu_util = 100.0 * cpu_time_s / elapsed_time_s / num_cpus::get() as f64;
        let count = self.request_count + self.error_count;

        let cycle_throughput = self.log.call_throughput();
        let cycle_throughput_ratio = self.rate_limit.map(|r| 100.0 * cycle_throughput.value / r);
        let req_throughput = self.log.req_throughput();
        let concurrency = self.log.mean_concurrency();
        let concurrency_ratio = 100.0 * concurrency.value / self.concurrency_limit.get() as f64;

        let cycle_time_percentiles: Vec<Mean> = Percentile::iter()
            .map(|p| self.log.cycle_time_percentile(p))
            .collect();
        let resp_time_percentiles: Vec<Mean> = Percentile::iter()
            .map(|p| self.log.resp_time_percentile(p))
            .collect();

        BenchmarkStats {
            start_time: self.start_time.into(),
            end_time: self.end_time.into(),
            elapsed_time_s,
            cpu_time_s,
            cpu_util,
            cycle_count: self.cycle_count,
            errors: self.errors.into_iter().collect(),
            error_count: self.error_count,
            errors_ratio: not_nan(100.0 * self.error_count as f64 / count as f64),
            request_count: self.request_count,
            requests_per_cycle: self.request_count as f64 / self.cycle_count as f64,
            cycle_throughput,
            cycle_throughput_ratio,
            req_throughput,
            cycle_time_ms: TimeDistribution {
                mean: self.log.cycle_time_ms(),
                percentiles: cycle_time_percentiles,
                distribution: distribution(&self.cycle_times_ns),
            },
            resp_time_ms: if self.request_count > 0 {
                Some(TimeDistribution {
                    mean: self.log.resp_time_ms(),
                    percentiles: resp_time_percentiles,
                    distribution: distribution(&self.resp_times_ns),
                })
            } else {
                None
            },
            concurrency,
            concurrency_ratio,
            log: self.log.samples,
        }
    }
}

#[cfg(test)]
mod test {
    use rand::distributions::Distribution;
    use rand::prelude::StdRng;
    use rand::SeedableRng;
    use statrs::distribution::Normal;
    use statrs::statistics::Statistics;

    use crate::stats::{t_test, Mean};

    /// Returns a random sample of size `len`.
    /// All data points i.i.d with N(`mean`, `std_dev`).
    fn random_vector(seed: usize, len: usize, mean: f64, std_dev: f64) -> Vec<f32> {
        let mut rng = StdRng::seed_from_u64(seed as u64);
        let distrib = Normal::new(mean, std_dev).unwrap();
        (0..len).map(|_| distrib.sample(&mut rng) as f32).collect()
    }

    /// Introduces a strong dependency between the observations,
    /// making it an AR(1) process
    fn make_autocorrelated(v: &mut [f32]) {
        for i in 1..v.len() {
            v[i] = 0.01 * v[i] + 0.99 * v[i - 1];
        }
    }

    /// Traditional standard error assuming i.i.d variables
    fn reference_err(v: &[f32]) -> f64 {
        v.iter().map(|x| *x as f64).std_dev() / (v.len() as f64).sqrt()
    }

    #[test]
    fn mean_err_no_auto_correlation() {
        let run_len = 10000;
        let mean = 1.0;
        let std_dev = 1.0;
        let weights = [1.0; 10000];
        for i in 0..10 {
            let v = random_vector(i, run_len, mean, std_dev);
            let err = super::long_run_err(mean, &v, &weights);
            let ref_err = reference_err(&v);
            assert!(err > 0.99 * ref_err);
            assert!(err < 1.2 * ref_err);
        }
    }

    #[test]
    fn mean_err_with_auto_correlation() {
        let run_len = 10000;
        let mean = 1.0;
        let std_dev = 1.0;
        let weights = [1.0; 10000];
        for i in 0..10 {
            let mut v = random_vector(i, run_len, mean, std_dev);
            make_autocorrelated(&mut v);
            let mean_err = super::long_run_err(mean, &v, &weights);
            let ref_err = reference_err(&v);
            assert!(mean_err > 6.0 * ref_err);
        }
    }

    #[test]
    fn t_test_same() {
        let mean1 = Mean {
            n: 100,
            value: 1.0,
            std_err: Some(0.1),
        };
        let mean2 = Mean {
            n: 100,
            value: 1.0,
            std_err: Some(0.2),
        };
        assert!(t_test(&mean1, &mean2) > 0.9999);
    }

    #[test]
    fn t_test_different() {
        let mean1 = Mean {
            n: 100,
            value: 1.0,
            std_err: Some(0.1),
        };
        let mean2 = Mean {
            n: 100,
            value: 1.3,
            std_err: Some(0.1),
        };
        assert!(t_test(&mean1, &mean2) < 0.05);
        assert!(t_test(&mean2, &mean1) < 0.05);

        let mean1 = Mean {
            n: 10000,
            value: 1.0,
            std_err: Some(0.0),
        };
        let mean2 = Mean {
            n: 10000,
            value: 1.329,
            std_err: Some(0.1),
        };
        assert!(t_test(&mean1, &mean2) < 0.0011);
        assert!(t_test(&mean2, &mean1) < 0.0011);
    }
}
