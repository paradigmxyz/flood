use crate::error::Result;
use crate::workload::Workload;
use crate::{config, Interval, WorkloadStats};
use futures::channel::mpsc::Sender;
use futures::SinkExt;
use std::time::Instant;

/// Responsible for periodically getting a snapshot of statistics from the `workload`
/// and sending them to the `output` channel. The sampling period is controlled by `sampling`.
/// Snapshot is not taken near the end of the run to avoid small final sample.
pub struct Sampler<'a> {
    run_duration: config::Interval,
    sampling: config::Interval,
    workload: &'a Workload,
    output: &'a mut Sender<Result<WorkloadStats>>,
    start_time: Instant,
    last_snapshot_time: Instant,
    last_snapshot_cycle: u64,
}

impl<'a> Sampler<'a> {
    pub fn new(
        run_duration: config::Interval,
        sampling: config::Interval,
        workload: &'a Workload,
        output: &'a mut Sender<Result<WorkloadStats>>,
    ) -> Sampler<'a> {
        let start_time = Instant::now();
        Sampler {
            run_duration,
            sampling,
            workload,
            output,
            start_time,
            last_snapshot_time: start_time,
            last_snapshot_cycle: 0,
        }
    }

    /// Should be called when a workload iteration finished.
    /// If there comes the time, it will send the stats to the output.
    pub async fn cycle_completed(&mut self, cycle: u64, now: Instant) {
        let current_interval_duration = now.saturating_duration_since(self.last_snapshot_time);
        let current_interval_cycle_count = cycle.saturating_sub(self.last_snapshot_cycle);

        // Don't snapshot if we're too close to the end of the run,
        // to avoid excessively small samples:
        let far_from_the_end = match self.run_duration {
            config::Interval::Time(d) => now + current_interval_duration / 2 < self.start_time + d,
            config::Interval::Count(count) => cycle + current_interval_cycle_count / 2 < count,
            config::Interval::Unbounded => true,
        };

        match self.sampling {
            Interval::Time(d) => {
                if now > self.last_snapshot_time + d && far_from_the_end {
                    self.send_stats().await;
                    // We may be running this slightly too late,
                    // so set the perfect time of the sample, so the next sample is slightly shorter.
                    // This way we avoid increasing the lag.
                    self.last_snapshot_time += d;
                    self.last_snapshot_cycle = cycle;
                }
            }
            Interval::Count(cnt) => {
                if cycle > self.last_snapshot_cycle + cnt && far_from_the_end {
                    self.send_stats().await;
                    self.last_snapshot_time = now;
                    // Similarly like with time, we might have been called
                    // when the counter already went a bit further than the target split point,
                    // so let's record the perfect (desired) cycle count so we don't
                    // increase the lag.
                    self.last_snapshot_cycle += cnt;
                }
            }
            Interval::Unbounded => {}
        }
    }

    /// Finishes the run by emiting the last sample
    pub async fn finish(mut self) {
        self.send_stats().await;
    }

    /// Fetches session statistics and sends them to the channel.
    async fn send_stats(&mut self) {
        let stats = self.workload.take_stats(Instant::now());
        self.output.send(Ok(stats)).await.unwrap();
    }
}
