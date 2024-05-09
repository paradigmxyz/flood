use crate::config::PlotCommand;
use crate::load_report_or_abort;
use crate::plot::SeriesKind::{ResponseTime, Throughput, SuccessRate, SuccessRateVsThroughput};
use crate::report::Report;
use crate::Result;
use itertools::Itertools;
use plotters::coord::ranged1d::{DefaultFormatting, KeyPointHint};
use plotters::coord::types::RangedCoordf32;
use plotters::prelude::full_palette::ORANGE;
use plotters::prelude::*;
use plotters_svg::SVGBackend;
use std::collections::BTreeSet;
use std::ops::Range;
use std::process::exit;

#[derive(Eq, PartialEq, Copy, Clone, Debug, Ord, PartialOrd)]
enum SeriesKind {
    ResponseTime,
    Throughput,
    SuccessRate,
    SuccessRateVsThroughput
}

impl SeriesKind {
    pub fn y_axis_label(&self) -> &str {
        match self {
            ResponseTime => "response time [ms]",
            Throughput => "throughput [req/s]",
            SuccessRate => "success rate [%]",
            SuccessRateVsThroughput => "success rate [%]",
        }
    }
}

struct Series {
    tags: Vec<String>,
    label: String,
    color_index: usize,
    symbol_index: usize,
    kind: SeriesKind,
    data: Vec<(f32, f32)>,
}

impl Series {
    fn full_label(&self) -> String {
        format!("{} [{}]", self.label, self.tags.join(", "))
    }
}

enum YSpec {
    Linear(RangedCoordf32),
    Log(LogCoord<f32>),
}

impl Ranged for YSpec {
    type FormatOption = DefaultFormatting;
    type ValueType = f32;

    fn map(&self, value: &Self::ValueType, limit: (i32, i32)) -> i32 {
        match self {
            YSpec::Linear(range) => range.map(value, limit),
            YSpec::Log(range) => range.map(value, limit),
        }
    }

    fn key_points<Hint: KeyPointHint>(&self, hint: Hint) -> Vec<Self::ValueType> {
        match self {
            YSpec::Linear(range) => range.key_points(hint),
            YSpec::Log(range) => range.key_points(hint),
        }
    }

    fn range(&self) -> Range<Self::ValueType> {
        match self {
            YSpec::Linear(range) => range.range(),
            YSpec::Log(range) => range.range(),
        }
    }
}

impl Series {
    pub fn max_value(&self, default: f32) -> f32 {
        self.data
            .iter()
            .map(|p| p.1)
            .reduce(f32::max)
            .unwrap_or(default)
    }

    pub fn min_value(&self, default: f32) -> f32 {
        self.data
            .iter()
            .map(|p| p.1)
            .reduce(f32::min)
            .unwrap_or(default)
    }

    pub fn max_time(&self) -> f32 {
        self.data.last().map(|s| s.0).unwrap_or_default()
    }
}

/// Dumps benchmark runs into an SVG file
pub async fn plot_graph(conf: PlotCommand) -> Result<()> {
    let reports = conf
        .reports
        .iter()
        .map(|r| load_report_or_abort(r))
        .collect_vec();
    assert!(!reports.is_empty());

    let data = data(&reports, &conf);
    let scales: BTreeSet<SeriesKind> = data.iter().map(|s| s.kind).collect();
    let scales = scales.into_iter().collect_vec();

    let max_time = data
        .iter()
        .map(Series::max_time)
        .reduce(f32::max)
        .unwrap_or(1.0);

    let min_value = data
        .iter()
        .map(|s| Series::min_value(s, 1.0))
        .reduce(f32::min)
        .unwrap_or(1.0);

    let max_value = data
        .iter()
        .map(|s| Series::max_value(s, 1.0))
        .reduce(f32::max)
        .unwrap_or(1.0);

    let primary_y_spec: YSpec = match scales.as_slice() {
        [ResponseTime] => YSpec::Log((min_value..max_value).log_scale().into()),
        [Throughput] => YSpec::Linear((0f32..max_value).into()),
        [SuccessRate] => YSpec::Linear((0f32..max_value).into()),
        [SuccessRateVsThroughput] => YSpec::Linear((0f32..max_value).into()),
        [] => {
            eprintln!("error: No data series selected. Add --throughput or --percentile options.");
            exit(1);
        }
        _ => {
            eprintln!(
                "error: Plotting throughput and response times in one graph is not supported."
            );
            exit(1);
        }
    };

    let output_path = conf
        .output
        .unwrap_or(reports[0].conf.default_output_file_name("svg"));
    let root = SVGBackend::new(&output_path, (2000, 1000)).into_drawing_area();
    root.fill(&WHITE).unwrap();

    let mut chart = ChartBuilder::on(&root)
        .margin(40)
        .x_label_area_size(60)
        .y_label_area_size(150)
        .build_cartesian_2d(0f32..max_time, primary_y_spec)
        .unwrap();

    if conf.success_rate && conf.throughput {
        chart
            .configure_mesh()
            .axis_desc_style(("sans-serif", 32).into_font())
            .x_desc("throughput [req/s]")
            .y_desc(scales[0].y_axis_label())
            .x_label_style(("sans-serif", 24).into_font())
            .y_label_style(("sans-serif", 24).into_font())
            .draw()
            .unwrap();
    } else {
        chart
            .configure_mesh()
            .axis_desc_style(("sans-serif", 32).into_font())
            .x_desc("time [s]")
            .y_desc(scales[0].y_axis_label())
            .x_label_style(("sans-serif", 24).into_font())
            .y_label_style(("sans-serif", 24).into_font())
            .draw()
            .unwrap();
    }

    let colors = [&RED, &BLUE, &GREEN, &ORANGE, &MAGENTA, &BLACK];
    const SYMBOL_SIZE: u32 = 6;

    for series in data {
        let color = colors[series.color_index];
        chart
            .draw_series(LineSeries::new(
                series.data.iter().cloned(),
                color.stroke_width(3),
            ))
            .unwrap();
        let points = series.data.iter();
        match series.symbol_index {
            0 => {
                chart
                    .draw_series(points.map(|point| Circle::new(*point, SYMBOL_SIZE, color)))
                    .unwrap()
                    .label(series.full_label())
                    .legend(|point| Circle::new(point, SYMBOL_SIZE, *color));
            }
            1 => {
                chart
                    .draw_series(
                        points.map(|point| TriangleMarker::new(*point, SYMBOL_SIZE, color)),
                    )
                    .unwrap()
                    .label(series.full_label())
                    .legend(|point| TriangleMarker::new(point, SYMBOL_SIZE, *color));
            }
            2 => {
                chart
                    .draw_series(points.map(|point| Cross::new(*point, SYMBOL_SIZE, color)))
                    .unwrap()
                    .label(series.full_label())
                    .legend(|point| Cross::new(point, SYMBOL_SIZE, *color));
            }
            _ => {}
        };
    }

    chart
        .configure_series_labels()
        .label_font(("sans-serif", 24).into_font())
        .margin(20)
        .legend_area_size(20)
        .border_style(BLACK)
        .background_style(WHITE.mix(0.7))
        .position(SeriesLabelPosition::UpperRight)
        .draw()
        .unwrap();

    eprintln!("Saved output image to: {}", output_path.display());
    Ok(())
}

fn data(reports: &[Report], conf: &PlotCommand) -> Vec<Series> {
    let mut series = vec![];
    for (color_index, report) in reports.iter().enumerate() {
        series.extend(report_series(report, color_index, conf));
    }
    series
}

/// Generates data from given report
fn report_series(report: &Report, color_index: usize, conf: &PlotCommand) -> Vec<Series> {
    let mut series = vec![];
    let mut percentiles = conf.percentiles.clone();
    percentiles.sort_by(|a, b| a.partial_cmp(b).unwrap().reverse());

    series.extend(resp_time_series(report, color_index, &percentiles));
    if conf.success_rate && conf.throughput {
        series.push(success_rate_v_throughput_series(report, color_index))
    } else {
        if conf.throughput {
            series.push(throughput_series(report, color_index))
        }
        if conf.success_rate {
            series.push(success_rate_series(report, color_index))
        }
    }
    series
}

fn resp_time_series(report: &Report, color_index: usize, percentiles: &[f64]) -> Vec<Series> {
    let mut series = percentiles
        .iter()
        .enumerate()
        .map(|(i, p)| Series {
            tags: report.conf.tags.clone(),
            label: format!("P{p}"),
            color_index,
            symbol_index: i,
            kind: ResponseTime,
            data: Vec::with_capacity(report.result.log.len()),
        })
        .collect_vec();

    for s in &report.result.log {
        for (i, p) in percentiles.iter().enumerate() {
            let time = s.time_s;
            let resp_time_ms =
                s.resp_time_histogram_ns.0.value_at_percentile(*p) as f32 / 1_000_000.0;
            series[i].data.push((time, resp_time_ms));
        }
    }
    series
}

fn throughput_series(report: &Report, color_index: usize) -> Series {
    Series {
        tags: report.conf.tags.clone(),
        label: String::from("throughput"),
        color_index,
        symbol_index: 0,
        kind: Throughput,
        data: report
            .result
            .log
            .iter()
            .map(|s| (s.time_s, s.req_throughput))
            .collect(),
    }
}

fn success_rate_series(report: &Report, color_index: usize) -> Series {
    Series {
        tags: report.conf.tags.clone(),
        label: String::from("success_rate"),
        color_index,
        symbol_index: 0,
        kind: SuccessRate,
        data: report
            .result
            .log
            .iter()
            .map(|s| (s.time_s, ((s.request_count - s.error_count) / s.request_count) as f32))
            .collect(),
    }
}

fn success_rate_v_throughput_series(report: &Report, color_index: usize) -> Series {
    Series {
        tags: report.conf.tags.clone(),
        label: String::from("throughput_vs_success_rate"),
        color_index,
        symbol_index: 2,
        kind: SuccessRateVsThroughput,
        data: report
            .result
            .log
            .iter()
            .map(|s| (s.req_throughput, ((s.request_count - s.error_count) / s.request_count) as f32))
            .collect(),
    }
}