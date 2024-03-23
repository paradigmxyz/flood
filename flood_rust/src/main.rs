use std::fs::File;
use std::io::{stdout, Write};
use std::path::Path;
use std::process::exit;
use std::sync::Arc;
use std::time::Duration;

use alloy_rpc_client::ClientBuilder;
use clap::Parser;
use hdrhistogram::serialization::interval_log::Tag;
use hdrhistogram::serialization::{interval_log, V2DeflateSerializer};
use tokio::runtime::{Builder, Runtime};

use config::RpcCommand;

use crate::config::{AppConfig, Command, HdrCommand, Interval, ShowCommand};
use crate::context::Context;
use crate::context::*;
use crate::cycle::BoundedCycleCounter;
use crate::error::{FloodError, Result};
use crate::exec::{par_execute, ExecutionOptions};
use crate::interrupt::InterruptHandler;
use crate::plot::plot_graph;
use crate::progress::Progress;
use crate::report::{Report, RpcConfigCmp};
use crate::sampler::Sampler;
use crate::stats::{BenchmarkCmp, BenchmarkStats, Recorder};
use crate::workload::{Workload, WorkloadStats};

mod config;
mod context;
mod cycle;
mod error;
mod exec;
mod histogram;
mod interrupt;
mod plot;
mod progress;
mod report;
mod sampler;
mod stats;
mod workload;

const VERSION: &str = env!("CARGO_PKG_VERSION");

#[global_allocator]
static ALLOC: jemallocator::Jemalloc = jemallocator::Jemalloc;

fn load_report_or_abort(path: &Path) -> Report {
    match Report::load(path) {
        Ok(r) => r,
        Err(e) => {
            eprintln!(
                "error: Failed to read report from {}: {}",
                path.display(),
                e
            );
            exit(1)
        }
    }
}

/// Connects to the eth node and returns the session
async fn connect(url: &Option<String>) -> Result<(Context, Option<NodeInfo>)> {
    let url = if url.is_none() {
        match std::env::var("HTTP_PROVIDER_URL")
            .map_err(FloodError::EnvVar) {
                Ok(url) => url,
                Err(_) => "http://127.0.0.1:8545".to_string()
            }
    } else {
        url.clone().unwrap()
    };
    // First have it connect to env var then to localhost
    eprintln!("info: Connecting to {:?}... ", url);
    let client = ClientBuilder::default().reqwest_http(url.parse().unwrap());
    let session = Context::new(client);
    let cluster_info = session.node_info().await?;
    eprintln!(
        "info: Connected to chain {}",
        cluster_info
            .as_ref()
            .map(|c| c.chain_id.to_string())
            .unwrap_or("unknown".to_string()),
    );
    Ok((session, cluster_info))
}

async fn rpc(conf: RpcCommand) -> Result<()> {
    let mut conf = conf.set_timestamp_if_empty();
    //TODO: simplify this? maybe option maybe a different workload
    let compare = conf.baseline.as_ref().map(|p| load_report_or_abort(p));

    let (session, node_info) = connect(&conf.rpc_url).await?;
    if let Some(node_info) = node_info {
        conf.cluster_name = Some(node_info.chain_id.to_string());
    }

    //TODO: Load from Clap
    let (call, params) = conf.parse_params().unwrap();
    println!("{:?}", params);
    //NOTE: this leaks memory and is a consequence of the limitations in the alloy crate.
    let call: &'static str = call.leak();
    let req = session.session.make_request(call, params).box_params();
    let runner = Workload::new(session.clone()?, req);
    let interrupt = Arc::new(InterruptHandler::install());
    if conf.warmup_duration.is_not_zero() {
        eprintln!("info: Warming up...");
        let warmup_options = ExecutionOptions {
            duration: conf.warmup_duration,
            rate: None,
            threads: conf.threads,
            concurrency: conf.concurrency,
        };
        par_execute(
            "Warming up...",
            &warmup_options,
            Interval::Unbounded,
            runner.clone()?,
            interrupt.clone(),
            !conf.quiet,
        )
        .await?;
    }

    if interrupt.is_interrupted() {
        return Err(FloodError::Interrupted);
    }

    eprintln!("info: Running benchmark...");

    println!(
        "{}",
        RpcConfigCmp {
            v1: &conf,
            v2: compare.as_ref().map(|c| &c.conf),
        }
    );

    //TODO: change to list of rates
    let exec_options = ExecutionOptions {
        duration: conf.run_duration,
        concurrency: conf.concurrency,
        rate: conf.rate,
        threads: conf.threads,
    };

    report::print_log_header();
    let stats = par_execute(
        "Running...",
        &exec_options,
        conf.sampling_interval,
        runner,
        interrupt.clone(),
        !conf.quiet,
    )
    .await?;

    let stats_cmp = BenchmarkCmp {
        v1: &stats,
        v2: compare.as_ref().map(|c| &c.result),
    };
    println!();
    println!("{}", &stats_cmp);

    let path = conf
        .output
        .clone()
        .unwrap_or_else(|| conf.default_output_file_name("json"));

    let report = Report::new(conf, stats);
    match report.save(&path) {
        Ok(()) => {
            eprintln!("info: Saved report to {}", path.display());
        }
        Err(e) => {
            eprintln!("error: Failed to save report to {}: {}", path.display(), e);
            exit(1);
        }
    }
    Ok(())
}

async fn show(conf: ShowCommand) -> Result<()> {
    let report1 = load_report_or_abort(&conf.report);
    let report2 = conf.baseline.map(|p| load_report_or_abort(&p));

    let config_cmp = RpcConfigCmp {
        v1: &report1.conf,
        v2: report2.as_ref().map(|r| &r.conf),
    };
    println!("{config_cmp}");

    let results_cmp = BenchmarkCmp {
        v1: &report1.result,
        v2: report2.as_ref().map(|r| &r.result),
    };
    println!("{results_cmp}");
    Ok(())
}

/// Reads histograms from the report and dumps them to an hdr log
async fn export_hdr_log(conf: HdrCommand) -> Result<()> {
    let tag_prefix = conf.tag.map(|t| t + ".").unwrap_or_default();
    if tag_prefix.chars().any(|c| ", \n\t".contains(c)) {
        eprintln!("error: Hdr histogram tags are not allowed to contain commas nor whitespace.");
        exit(255);
    }

    let report = load_report_or_abort(&conf.report);
    let stdout = stdout();
    let output_file: File;
    let stdout_stream;
    let mut out: Box<dyn Write> = match conf.output {
        Some(path) => {
            output_file = File::create(&path).map_err(|e| FloodError::OutputFileCreate(path, e))?;
            Box::new(output_file)
        }
        None => {
            stdout_stream = stdout.lock();
            Box::new(stdout_stream)
        }
    };

    let mut serializer = V2DeflateSerializer::new();
    let mut log_writer = interval_log::IntervalLogWriterBuilder::new()
        .add_comment(format!("[Logged with Latte {VERSION}]").as_str())
        .with_start_time(report.result.start_time.into())
        .with_base_time(report.result.start_time.into())
        .with_max_value_divisor(1000000.0) // ms
        .begin_log_with(&mut out, &mut serializer)
        .unwrap();

    for sample in &report.result.log {
        let interval_start_time = Duration::from_millis((sample.time_s * 1000.0) as u64);
        let interval_duration = Duration::from_millis((sample.duration_s * 1000.0) as u64);
        log_writer.write_histogram(
            &sample.cycle_time_histogram_ns.0,
            interval_start_time,
            interval_duration,
            Tag::new(format!("{tag_prefix}cycles").as_str()),
        )?;
        log_writer.write_histogram(
            &sample.resp_time_histogram_ns.0,
            interval_start_time,
            interval_duration,
            Tag::new(format!("{tag_prefix}requests").as_str()),
        )?;
    }
    Ok(())
}

async fn async_main(command: Command) -> Result<()> {
    match command {
        Command::Rpc(config) => rpc(config).await?,
        Command::Show(config) => show(config).await?,
        Command::Hdr(config) => export_hdr_log(config).await?,
        Command::Plot(config) => plot_graph(config).await?,
    }
    Ok(())
}

fn init_runtime(thread_count: usize) -> std::io::Result<Runtime> {
    if thread_count == 1 {
        Builder::new_current_thread().enable_all().build()
    } else {
        Builder::new_multi_thread()
            .worker_threads(thread_count)
            .enable_all()
            .build()
    }
}

fn main() {
    tracing_subscriber::fmt::init();
    let command = AppConfig::parse().command;
    let thread_count = match &command {
        Command::Rpc(cmd) => cmd.threads.get(),
        _ => 1,
    };
    let runtime = init_runtime(thread_count);
    if let Err(e) = runtime.unwrap().block_on(async_main(command)) {
        eprintln!("error: {e}");
        exit(128);
    }
}
