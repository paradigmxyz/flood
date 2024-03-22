//! Implementation of the main benchmarking loop

use futures::channel::mpsc::{channel, Receiver, Sender};
use futures::{SinkExt, Stream, StreamExt};
use itertools::Itertools;
use status_line::StatusLine;
use std::cmp::max;
use std::future::ready;
use std::num::NonZeroUsize;
use std::sync::Arc;
use std::time::Instant;
use tokio_stream::wrappers::IntervalStream;

use crate::error::Result;
use crate::workload::Workload;
use crate::{
    BenchmarkStats, BoundedCycleCounter, InterruptHandler, Interval, Progress, Recorder, Sampler,
    WorkloadStats,
};

/// Returns a stream emitting `rate` events per second.
fn interval_stream(rate: f64) -> IntervalStream {
    let interval = tokio::time::Duration::from_nanos(max(1, (1000000000.0 / rate) as u64));
    IntervalStream::new(tokio::time::interval(interval))
}

/// Runs a stream of workload cycles till completion in the context of the current task.
/// Periodically sends workload statistics to the `out` channel.
///
/// # Parameters
/// - stream: a stream of cycle numbers; None means the end of the stream
/// - workload: defines the function to call
/// - cycle_counter: shared cycle numbers provider
/// - concurrency: the maximum number of pending workload calls
/// - sampling: controls when to output workload statistics
/// - progress: progress bar notified about each successful cycle
/// - interrupt: allows for terminating the stream early
/// - out: the channel to receive workload statistics
///
#[allow(clippy::too_many_arguments)] // todo: refactor
async fn run_stream<T>(
    stream: impl Stream<Item = T> + std::marker::Unpin,
    workload: Workload,
    cycle_counter: BoundedCycleCounter,
    concurrency: NonZeroUsize,
    sampling: Interval,
    interrupt: Arc<InterruptHandler>,
    progress: Arc<StatusLine<Progress>>,
    mut out: Sender<Result<WorkloadStats>>,
) {
    workload.reset(Instant::now());

    let mut iter_counter = cycle_counter;
    let mut sampler = Sampler::new(iter_counter.duration, sampling, &workload, &mut out);

    let mut result_stream = stream
        .map(|_| iter_counter.next())
        .take_while(|i| ready(i.is_some()))
        // unconstrained to workaround quadratic complexity of buffer_unordered ()
        .map(|i| tokio::task::unconstrained(workload.run(i.unwrap())))
        .buffer_unordered(concurrency.get())
        .inspect(|_| progress.tick());

    while let Some(res) = result_stream.next().await {
        match res {
            Ok((iter, end_time)) => sampler.cycle_completed(iter, end_time).await,
            Err(e) => {
                out.send(Err(e)).await.unwrap();
                return;
            }
        }
        if interrupt.is_interrupted() {
            break;
        }
    }
    // Send the statistics of remaining requests
    sampler.finish().await;
}

/// Launches a new worker task that runs a series of invocations of the workload function.
///
/// The task will run as long as `deadline` produces new cycle numbers.
/// The task updates the `progress` bar after each successful cycle.
///
/// Returns a stream where workload statistics are published.
fn spawn_stream(
    concurrency: NonZeroUsize,
    rate: Option<f64>,
    sampling: Interval,
    workload: Workload,
    iter_counter: BoundedCycleCounter,
    interrupt: Arc<InterruptHandler>,
    progress: Arc<StatusLine<Progress>>,
) -> Receiver<Result<WorkloadStats>> {
    let (tx, rx) = channel(1);

    tokio::spawn(async move {
        match rate {
            Some(rate) => {
                let stream = interval_stream(rate);
                run_stream(
                    stream,
                    workload,
                    iter_counter,
                    concurrency,
                    sampling,
                    interrupt,
                    progress,
                    tx,
                )
                .await
            }
            None => {
                let stream = futures::stream::repeat_with(|| ());
                run_stream(
                    stream,
                    workload,
                    iter_counter,
                    concurrency,
                    sampling,
                    interrupt,
                    progress,
                    tx,
                )
                .await
            }
        }
    });
    rx
}

/// Receives one item from each of the streams.
/// Streams that are closed are ignored.
async fn receive_one_of_each<T, S>(streams: &mut [S]) -> Vec<T>
where
    S: Stream<Item = T> + Unpin,
{
    let mut items = Vec::with_capacity(streams.len());
    for s in streams {
        if let Some(item) = s.next().await {
            items.push(item);
        }
    }
    items
}

/// Controls the intensity of requests sent to the server
pub struct ExecutionOptions {
    /// How long to execute
    pub duration: Interval,
    /// Maximum rate of requests in requests per second, `None` means no limit
    pub rate: Option<f64>,
    /// Number of parallel threads of execution
    pub threads: NonZeroUsize,
    /// Number of outstanding async requests per each thread
    pub concurrency: NonZeroUsize,
}

/// Executes the given function many times in parallel.
/// Draws a progress bar.
/// Returns the statistics such as throughput or duration histogram.
///
/// # Parameters
///   - `name`: text displayed next to the progress bar
///   - `count`: number of cycles
///   - `exec_options`: controls execution options such as parallelism level and rate
///   - `workload`: encapsulates a set of queries to execute
pub async fn par_execute(
    name: &str,
    exec_options: &ExecutionOptions,
    sampling: Interval,
    workload: Workload,
    signals: Arc<InterruptHandler>,
    show_progress: bool,
) -> Result<BenchmarkStats> {
    let thread_count = exec_options.threads.get();
    let concurrency = exec_options.concurrency;
    //TODO change to list of rates
    let rate = exec_options.rate;
    let progress = match exec_options.duration {
        Interval::Count(count) => Progress::with_count(name.to_string(), count),
        Interval::Time(duration) => Progress::with_duration(name.to_string(), duration),
        Interval::Unbounded => unreachable!(),
    };
    let progress_opts = status_line::Options {
        initially_visible: show_progress,
        ..Default::default()
    };
    let progress = Arc::new(StatusLine::with_options(progress, progress_opts));
    let deadline = BoundedCycleCounter::new(exec_options.duration);
    let mut streams = Vec::with_capacity(thread_count);
    let mut stats = Recorder::start(rate, concurrency);

    for _ in 0..thread_count {
        let s = spawn_stream(
            concurrency,
            rate.map(|r| r / (thread_count as f64)),
            sampling,
            workload.clone()?,
            deadline.share(),
            signals.clone(),
            progress.clone(),
        );
        streams.push(s);
    }

    loop {
        let partial_stats: Vec<_> = receive_one_of_each(&mut streams)
            .await
            .into_iter()
            .try_collect()?;

        if partial_stats.is_empty() {
            break;
        }

        let aggregate = stats.record(&partial_stats);
        if sampling.is_bounded() {
            progress.set_visible(false);
            println!("{aggregate}");
            progress.set_visible(show_progress);
        }
    }

    Ok(stats.finish())
}
