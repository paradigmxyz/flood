use hdrhistogram::Histogram;
use rand::distributions::weighted::alias_method::WeightedIndex;
use rand::distributions::Distribution;
use rand::rngs::ThreadRng;
use rand::thread_rng;

/// Bootstraps a random population sample based on given distribution.
/// See: https://en.wikipedia.org/wiki/Bootstrapping_(statistics)
pub struct Bootstrap {
    values: Vec<u64>,
    index: WeightedIndex<u64>,
    rng: ThreadRng,
}

impl Bootstrap {
    pub fn new(histogram: &Histogram<u64>) -> Bootstrap {
        let mut values = Vec::new();
        let mut weights = Vec::new();
        for v in histogram.iter_recorded() {
            values.push(histogram.median_equivalent(v.value_iterated_to()));
            weights.push(v.count_since_last_iteration());
        }
        Bootstrap {
            values,
            index: WeightedIndex::new(weights).unwrap(),
            rng: thread_rng(),
        }
    }

    pub fn sample(&mut self) -> u64 {
        self.values[self.index.sample(&mut self.rng)]
    }
}

#[cfg(test)]
mod test {
    use super::*;
    use statrs::statistics::Mean;
    use statrs::statistics::Statistics;

    #[test]
    fn mean() {
        let mut h1 = Histogram::<u64>::new(3).unwrap();
        for i in 10..100001 {
            h1.record(i);
        }
        //h1.record(100000);

        let mean = h1.mean();
        println!("Mean: {}", mean);
        println!("Stderr: {}", h1.stdev() / (h1.len() as f64).sqrt());

        let mut bootstrap = Bootstrap::new(&h1);
        let mut means = Vec::new();
        for j in 0..10 {
            let mut h = Vec::with_capacity(100000);
            for i in 0..100000 {
                h.push(bootstrap.sample() as f64);
            }
            means.push(h.mean());
        }

        println!("Means mean: {}", means.iter().mean());
        println!("Means stddev: {}", means.iter().std_dev());
    }
}
