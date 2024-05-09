use core::fmt;
use std::fmt::{Display, Formatter};
use std::num::NonZeroUsize;
use std::path::Path;
use std::{fs, io};

use chrono::{Local, NaiveDateTime, TimeZone};
use console::{pad_str, style, Alignment};
use err_derive::*;
use itertools::Itertools;
use serde::{Deserialize, Serialize};
use statrs::statistics::Statistics;
use strum::IntoEnumIterator;

use crate::config::RpcCommand;
use crate::stats::{
    BenchmarkCmp, BenchmarkStats, Bucket, Mean, Percentile, Sample, Significance, TimeDistribution,
};

/// A standard error is multiplied by this factor to get the error margin.
/// For a normally distributed random variable,
/// this should give us 0.999 confidence the expected value is within the (result +- error) range.
const ERR_MARGIN: f64 = 3.29;

#[derive(Debug, Error)]
pub enum ReportLoadError {
    #[error(display = "{}", _0)]
    IO(#[source] io::Error),
    #[error(display = "{}", _0)]
    Deserialize(#[source] serde_json::Error),
}

/// Keeps all data we want to save in a report:
/// run metadata, configuration and results
#[derive(Serialize, Deserialize)]
pub struct Report {
    pub conf: RpcCommand,
    pub percentiles: Vec<f32>,
    pub result: BenchmarkStats,
}

impl Report {
    /// Creates a new report from given configuration and results
    pub fn new(conf: RpcCommand, result: BenchmarkStats) -> Report {
        let percentiles: Vec<f32> = Percentile::iter().map(|p| p.value() as f32).collect();
        Report {
            conf,
            percentiles,
            result,
        }
    }
    /// Loads benchmark results from a JSON file
    pub fn load(path: &Path) -> Result<Report, ReportLoadError> {
        let file = fs::File::open(path)?;
        let report = serde_json::from_reader(file)?;
        Ok(report)
    }

    /// Saves benchmark results to a JSON file
    pub fn save(&self, path: &Path) -> io::Result<()> {
        let f = fs::File::create(path)?;
        serde_json::to_writer_pretty(f, &self)?;
        Ok(())
    }
}

/// A displayable, optional value with an optional error.
/// Controls formatting options such as precision.
/// Thanks to this wrapper we can format all numeric values in a consistent way.
pub struct Quantity<T> {
    pub value: Option<T>,
    pub error: Option<T>,
    pub precision: usize,
}

impl<T> Quantity<T> {
    pub fn new(value: Option<T>) -> Quantity<T> {
        Quantity {
            value,
            error: None,
            precision: 0,
        }
    }

    pub fn with_precision(mut self, precision: usize) -> Self {
        self.precision = precision;
        self
    }

    pub fn with_error(mut self, e: Option<T>) -> Self {
        self.error = e;
        self
    }
}

impl<T: Display> Quantity<T> {
    fn format_error(&self) -> String {
        match &self.error {
            None => "".to_owned(),
            Some(e) => format!("± {:<6.prec$}", e, prec = self.precision),
        }
    }
}

impl<T: Display> From<T> for Quantity<T> {
    fn from(value: T) -> Self {
        Quantity::new(Some(value))
    }
}

impl<T: Display> From<Option<T>> for Quantity<T> {
    fn from(value: Option<T>) -> Self {
        Quantity::new(value)
    }
}

impl From<Mean> for Quantity<f64> {
    fn from(m: Mean) -> Self {
        Quantity::new(Some(m.value)).with_error(m.std_err.map(|e| e * ERR_MARGIN))
    }
}

impl From<Option<Mean>> for Quantity<f64> {
    fn from(m: Option<Mean>) -> Self {
        Quantity::new(m.map(|mean| mean.value))
            .with_error(m.and_then(|mean| mean.std_err.map(|e| e * ERR_MARGIN)))
    }
}

impl From<&TimeDistribution> for Quantity<f64> {
    fn from(td: &TimeDistribution) -> Self {
        Quantity::from(td.mean)
    }
}

impl From<&Option<TimeDistribution>> for Quantity<f64> {
    fn from(td: &Option<TimeDistribution>) -> Self {
        Quantity::from(td.as_ref().map(|td| td.mean))
    }
}

impl<T: Display> Display for Quantity<T> {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        match &self.value {
            None => write!(f, "{}", " ".repeat(18)),
            Some(v) => write!(
                f,
                "{value:9.prec$} {error:8}",
                value = style(v).bright().for_stdout(),
                prec = self.precision,
                error = style(self.format_error()).dim().for_stdout(),
            ),
        }
    }
}

/// Wrapper for displaying an optional value.
/// If value is `Some`, displays the original value.
/// If value is `None`, displays nothing (empty string).
struct OptionDisplay<T>(Option<T>);

impl<T: Display> Display for OptionDisplay<T> {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        match &self.0 {
            None => write!(f, ""),
            Some(v) => write!(f, "{v}"),
        }
    }
}

trait Rational {
    fn ratio(a: Self, b: Self) -> Option<f32>;
}

impl Rational for f32 {
    fn ratio(a: Self, b: Self) -> Option<f32> {
        Some(a / b)
    }
}

impl Rational for f64 {
    fn ratio(a: Self, b: Self) -> Option<f32> {
        Some((a / b) as f32)
    }
}

impl Rational for u64 {
    fn ratio(a: Self, b: Self) -> Option<f32> {
        Some(a as f32 / b as f32)
    }
}

impl Rational for i64 {
    fn ratio(a: Self, b: Self) -> Option<f32> {
        Some(a as f32 / b as f32)
    }
}

impl Rational for usize {
    fn ratio(a: Self, b: Self) -> Option<f32> {
        Some(a as f32 / b as f32)
    }
}

impl Rational for NonZeroUsize {
    fn ratio(a: Self, b: Self) -> Option<f32> {
        Some(a.get() as f32 / b.get() as f32)
    }
}

impl<T: Rational> Rational for OptionDisplay<T> {
    fn ratio(a: Self, b: Self) -> Option<f32> {
        a.0.and_then(|a| b.0.and_then(|b| Rational::ratio(a, b)))
    }
}

impl<T: Rational + Display> Rational for Quantity<T> {
    fn ratio(a: Self, b: Self) -> Option<f32> {
        a.value
            .and_then(|a| b.value.and_then(|b| Rational::ratio(a, b)))
    }
}

impl Rational for String {
    fn ratio(_a: Self, _b: Self) -> Option<f32> {
        None
    }
}

impl Rational for &str {
    fn ratio(_a: Self, _b: Self) -> Option<f32> {
        None
    }
}

impl Display for Significance {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        let levels = [0.000001, 0.00001, 0.0001, 0.001, 0.01];
        let stars = "*".repeat(levels.iter().filter(|&&l| l > self.0).count());
        let s = format!("{:7.5}  {:5}", self.0, stars);
        if self.0 <= 0.01 {
            write!(f, "{}", style(s).cyan().bright())
        } else {
            write!(f, "{}", style(s).dim())
        }
    }
}
/// A single line of text report
struct Line<M, V, F>
where
    M: Display + Rational,
    F: Fn(V) -> M,
{
    /// Text label
    pub label: String,
    /// Unit of measurement
    pub unit: String,
    /// 1 means the more of the quantity the better, -1 means the more of it the worse, 0 is neutral
    pub orientation: i8,
    /// First object to measure
    pub v1: V,
    /// Second object to measure
    pub v2: Option<V>,
    /// Statistical significance level
    pub significance: Option<Significance>,
    /// Measurement function
    pub f: F,
}

impl<M, V, F> Line<M, V, F>
where
    M: Display + Rational,
    V: Copy,
    F: Fn(V) -> M,
{
    fn new(label: String, unit: String, orientation: i8, v1: V, v2: Option<V>, f: F) -> Self {
        Line {
            label,
            unit,
            orientation,
            v1,
            v2,
            significance: None,
            f,
        }
    }

    fn into_box(self) -> Box<Self> {
        Box::new(self)
    }

    fn with_orientation(mut self, orientation: i8) -> Self {
        self.orientation = orientation;
        self
    }

    fn with_significance(mut self, s: Option<Significance>) -> Self {
        self.significance = s;
        self
    }

    /// Measures the object `v` by applying `f` to it and formats the measurement result.
    /// If the object is None, returns an empty string.
    fn fmt_measurement(&self, v: Option<V>) -> String {
        v.map(|v| format!("{}", (self.f)(v)))
            .unwrap_or_else(|| "".to_owned())
    }

    /// Computes the relative difference between v2 and v1 as: 100.0 * f(v2) / f(v1) - 100.0.
    /// Then formats the difference as percentage.
    /// If any of the values are missing, returns an empty String
    fn fmt_relative_change(&self, direction: i8, significant: bool) -> String {
        self.v2
            .and_then(|v2| {
                let m1 = (self.f)(self.v1);
                let m2 = (self.f)(v2);
                let ratio = Rational::ratio(m1, m2);
                ratio.map(|r| {
                    let mut diff = 100.0 * (r - 1.0);
                    if diff.is_nan() {
                        diff = 0.0;
                    }
                    let good = diff * direction as f32;
                    let diff = format!("{diff:+7.1}%");
                    let styled = if good == 0.0 || !significant {
                        style(diff).dim()
                    } else if good > 0.0 {
                        style(diff).bright().green()
                    } else {
                        style(diff).bright().red()
                    };
                    format!("{styled}")
                })
            })
            .unwrap_or_default()
    }

    fn fmt_unit(&self) -> String {
        match self.unit.as_str() {
            "" => "".to_string(),
            u => format!("[{u}]"),
        }
    }
}

impl<M, V, F> Display for Line<M, V, F>
where
    M: Display + Rational,
    F: Fn(V) -> M,
    V: Copy,
{
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        // if v2 defined, put v2 on left
        let m1 = self.fmt_measurement(self.v2.or(Some(self.v1)));
        let m2 = self.fmt_measurement(self.v2.map(|_| self.v1));
        let is_significant = match self.significance {
            None => false,
            Some(s) => s.0 <= 0.01,
        };
        write!(
            f,
            "{label:>16} {unit:>9}  {m1} {m2}  {cmp:6}     {signif}",
            label = style(&self.label).yellow().bold().for_stdout(),
            unit = style(self.fmt_unit()).yellow(),
            m1 = pad_str(m1.as_str(), 30, Alignment::Left, None),
            m2 = pad_str(m2.as_str(), 30, Alignment::Left, None),
            cmp = self.fmt_relative_change(self.orientation, is_significant),
            signif = match &self.significance {
                Some(s) => format!("{s}"),
                None => "".to_owned(),
            }
        )
    }
}

const REPORT_WIDTH: usize = 124;

fn fmt_section_header(name: &str) -> String {
    format!(
        "{} {}",
        style(name).yellow().bold().bright().for_stdout(),
        style("═".repeat(REPORT_WIDTH - name.len() - 1))
            .yellow()
            .bold()
            .bright()
            .for_stdout()
    )
}

fn fmt_horizontal_line() -> String {
    format!("{}", style("─".repeat(REPORT_WIDTH)).yellow().dim())
}

fn fmt_cmp_header(display_significance: bool) -> String {
    let header = format!(
        "{} {} {}",
        " ".repeat(27),
        "───────────── A ─────────────  ────────────── B ────────────     Change    ",
        if display_significance {
            "P-value  Signif."
        } else {
            ""
        }
    );
    format!("{}", style(header).yellow().bold().for_stdout())
}
pub struct RpcConfigCmp<'a> {
    pub v1: &'a RpcCommand,
    pub v2: Option<&'a RpcCommand>,
}

impl RpcConfigCmp<'_> {
    fn line<S, M, F>(&self, label: S, unit: &str, f: F) -> Box<Line<M, &RpcCommand, F>>
    where
        S: ToString,
        M: Display + Rational,
        F: Fn(&RpcCommand) -> M,
    {
        Box::new(Line::new(
            label.to_string(),
            unit.to_string(),
            0,
            self.v1,
            self.v2,
            f,
        ))
    }

    fn format_time(&self, conf: &RpcCommand, format: &str) -> String {
        conf.timestamp
            .and_then(|ts| {
                NaiveDateTime::from_timestamp_opt(ts, 0)
                    .map(|utc| Local.from_utc_datetime(&utc).format(format).to_string())
            })
            .unwrap_or_default()
    }

}

impl<'a> Display for RpcConfigCmp<'a> {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        writeln!(f, "{}", fmt_section_header("CONFIG"))?;
        if self.v2.is_some() {
            writeln!(f, "{}", fmt_cmp_header(false))?;
        }

        let lines: Vec<Box<dyn Display>> = vec![
            self.line("Date", "", |conf| self.format_time(conf, "%a, %d %b %Y")),
            self.line("Time", "", |conf| self.format_time(conf, "%H:%M:%S %z")),
            self.line("Cluster", "", |conf| {
                OptionDisplay(conf.cluster_name.clone())
            }),
            self.line("Chain ID", "", |conf| OptionDisplay(conf.chain_id.clone())),
            self.line("Tags", "", |conf| conf.tags.iter().join(", ")),
        ];

        for l in lines {
            writeln!(f, "{l}")?;
        }

        writeln!(f, "{}", fmt_horizontal_line()).unwrap();

        let lines: Vec<Box<dyn Display>> = vec![
            self.line("Threads", "", |conf| Quantity::from(conf.threads)),
            self.line("Connection(s)", "", |conf| format!("{value:9}", value = conf.rpc_url.iter().join(", "))),
            self.line("Concurrency", "reqs", |conf| {
                Quantity::from(conf.concurrency)
            }),
            self.line("Reqs / Workload", "reqs", |conf| {
                Quantity::from(conf.num_req)
            }),
            self.line("Max Rate(s)", "req/s", |conf| 
                match &conf.rate {
                    Some(rates) => format!("{value:9}", value = rates.into_iter().map(|r| { format!("{}", style(r).bright().for_stdout()) }).collect::<Vec<String>>().join(", ")),
                    None => format!("{value:9}", value = style("MAX RATE").bright().for_stdout()),
                }),
            self.line("Warmup", "s", |conf| {
                Quantity::from(conf.warmup_duration.seconds())
            }),
            self.line("└─", "ops", |conf| {
                Quantity::from(conf.warmup_duration.count())
            }),
            self.line("Run time", "s", |conf| {
                Quantity::from(conf.run_duration.seconds()).with_precision(1)
            }),
            self.line("└─", "ops", |conf| {
                Quantity::from(conf.run_duration.count())
            }),
            self.line("Sampling", "s", |conf| {
                Quantity::from(conf.sampling_interval.seconds()).with_precision(1)
            }),
            self.line("└─", "", |conf| {
                Quantity::from(conf.sampling_interval.count())
            }),
        ];

        for l in lines {
            writeln!(f, "{l}")?;
        }
        Ok(())
    }
}

pub fn print_log_header() {
    println!("{}", fmt_section_header("LOG"));
    println!("{}", style("    Time  ───── Throughput ─────  ────────────────────────────────── Response times [ms] ───────────────────────────────────").yellow().bold().for_stdout());
    println!("{}", style("     [s]      [op/s]     [req/s]         Min        25        50        75        90        95        99      99.9       Max").yellow().for_stdout());
}

impl Display for Sample {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "{:8.3} {:11.0} {:11.0}   {:9.3} {:9.3} {:9.3} {:9.3} {:9.3} {:9.3} {:9.3} {:9.3} {:9.3}",
            self.time_s + self.duration_s,
            self.cycle_throughput,
            self.req_throughput,
            self.resp_time_percentiles[Percentile::Min as usize],
            self.resp_time_percentiles[Percentile::P25 as usize],
            self.resp_time_percentiles[Percentile::P50 as usize],
            self.resp_time_percentiles[Percentile::P75 as usize],
            self.resp_time_percentiles[Percentile::P90 as usize],
            self.resp_time_percentiles[Percentile::P95 as usize],
            self.resp_time_percentiles[Percentile::P99 as usize],
            self.resp_time_percentiles[Percentile::P99_9 as usize],
            self.resp_time_percentiles[Percentile::Max as usize]
        )
    }
}

impl BenchmarkCmp<'_> {
    fn line<S, M, F>(&self, label: S, unit: &str, f: F) -> Box<Line<M, &BenchmarkStats, F>>
    where
        S: ToString,
        M: Display + Rational,
        F: Fn(&BenchmarkStats) -> M,
    {
        Box::new(Line::new(
            label.to_string(),
            unit.to_string(),
            0,
            self.v1,
            self.v2,
            f,
        ))
    }
}

/// Formats all benchmark stats
impl<'a> Display for BenchmarkCmp<'a> {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        writeln!(f, "{}", fmt_section_header("SUMMARY STATS"))?;
        if self.v2.is_some() {
            writeln!(f, "{}", fmt_cmp_header(true))?;
        }

        let summary: Vec<Box<dyn Display>> = vec![
            self.line("Elapsed time", "s", |s| {
                Quantity::from(s.elapsed_time_s).with_precision(3)
            }),
            self.line("CPU time", "s", |s| {
                Quantity::from(s.cpu_time_s).with_precision(3)
            }),
            self.line("CPU utilisation", "%", |s| {
                Quantity::from(s.cpu_util).with_precision(1)
            }),
            self.line("Workloads", "ops", |s| Quantity::from(s.cycle_count)),
            self.line("Successful Reqs", "reqs", |s| Quantity::from(s.request_count - s.error_count)),
            self.line("└─", "%", |s| {
                Quantity::from(s.errors_ratio).with_precision(1)
            }),
            self.line("Failed Reqs", "reqs", |s| Quantity::from(s.error_count)),
            self.line("└─", "%", |s| {
                Quantity::from(s.errors_ratio).with_precision(1)
            }),
            self.line("Total Requests", "reqs", |s| Quantity::from(s.request_count)),
            self.line("└─", "req/op", |s| {
                Quantity::from(s.requests_per_cycle).with_precision(1)
            }),
            self.line("Samples", "", |s| Quantity::from(s.log.len())),
            self.line("Mean sample size", "op", |s| {
                Quantity::from(s.log.iter().map(|s| s.cycle_count as f64).mean())
            }),
            self.line("└─", "req", |s| {
                Quantity::from(s.log.iter().map(|s| s.request_count as f64).mean())
            }),
            self.line("Concurrency", "req", |s| Quantity::from(s.concurrency)),
            self.line("└─", "%", |s| Quantity::from(s.concurrency_ratio)),
            self.line("Throughput", "op/s", |s| Quantity::from(s.cycle_throughput))
                .with_significance(self.cmp_cycle_throughput())
                .with_orientation(1)
                .into_box(),
            self.line("├─", "req/s", |s| Quantity::from(s.req_throughput))
                .with_significance(self.cmp_req_throughput())
                .with_orientation(1)
                .into_box(),
            self.line("Mean workload time", "ms", |s| {
                Quantity::from(&s.cycle_time_ms).with_precision(3)
            })
            .with_significance(self.cmp_mean_resp_time())
            .with_orientation(-1)
            .into_box(),
            self.line("Mean resp. time", "ms", |s| {
                Quantity::from(s.resp_time_ms.as_ref().map(|rt| rt.mean)).with_precision(3)
            })
            .with_significance(self.cmp_mean_resp_time())
            .with_orientation(-1)
            .into_box(),
        ];

        for l in summary {
            writeln!(f, "{l}")?;
        }
        writeln!(f)?;

        if self.v1.request_count > 0 {
            let resp_time_percentiles = [
                Percentile::Min,
                Percentile::P25,
                Percentile::P50,
                Percentile::P75,
                Percentile::P90,
                Percentile::P95,
                Percentile::P98,
                Percentile::P99,
                Percentile::P99_9,
                Percentile::P99_99,
                Percentile::Max,
            ];
            writeln!(f)?;
            writeln!(f, "{}", fmt_section_header("RESPONSE TIMES [ms]"))?;
            if self.v2.is_some() {
                writeln!(f, "{}", fmt_cmp_header(true))?;
            }

            for p in resp_time_percentiles.iter() {
                let l = self
                    .line(p.name(), "", |s| {
                        let rt = s
                            .resp_time_ms
                            .as_ref()
                            .map(|rt| rt.percentiles[*p as usize]);
                        Quantity::from(rt).with_precision(3)
                    })
                    .with_orientation(-1)
                    .with_significance(self.cmp_resp_time_percentile(*p));
                writeln!(f, "{l}")?;
            }

            writeln!(f)?;
            writeln!(f, "{}", fmt_section_header("RESPONSE TIME DISTRIBUTION"))?;
            writeln!(f, "{}", style("── Resp. time [ms] ──  ────────────────────────────────────────────── Count ────────────────────────────────────────────────").yellow().bold().for_stdout())?;
            let zero = Bucket {
                percentile: 0.0,
                duration_ms: 0.0,
                count: 0,
                cumulative_count: 0,
            };
            let dist = &self.v1.resp_time_ms.as_ref().unwrap().distribution;
            let max_count = dist.iter().map(|b| b.count).max().unwrap_or(1);
            for (low, high) in ([zero].iter().chain(dist)).tuple_windows() {
                writeln!(
                    f,
                    "{:8.1} {} {:8.1}  {:9} {:6.2}%  {}",
                    style(low.duration_ms).yellow().for_stdout(),
                    style("...").yellow().for_stdout(),
                    style(high.duration_ms).yellow().for_stdout(),
                    high.count,
                    high.percentile - low.percentile,
                    style("▪".repeat((82 * high.count / max_count) as usize))
                        .dim()
                        .for_stdout()
                )?;
                if high.cumulative_count == self.v1.request_count {
                    break;
                }
            }
        }

        if self.v1.error_count > 0 {
            writeln!(f)?;
            writeln!(f, "{}", fmt_section_header("ERRORS"))?;
            for e in self.v1.errors.iter() {
                writeln!(f, "{e}")?;
            }
        }
        Ok(())
    }
}
