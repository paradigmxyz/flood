use console::style;
use hytra::TrAdder;
use std::cmp::min;
use std::fmt::{Display, Formatter};

use tokio::time::{Duration, Instant};

enum ProgressBound {
    Duration(Duration),
    Count(u64),
}

pub struct Progress {
    start_time: Instant,
    bound: ProgressBound,
    pos: TrAdder<u64>,
    msg: String,
}

impl Progress {
    pub fn with_duration(msg: String, max_time: Duration) -> Progress {
        Progress {
            start_time: Instant::now(),
            bound: ProgressBound::Duration(max_time),
            pos: TrAdder::new(),
            msg,
        }
    }

    pub fn with_count(msg: String, count: u64) -> Progress {
        Progress {
            start_time: Instant::now(),
            bound: ProgressBound::Count(count),
            pos: TrAdder::new(),
            msg,
        }
    }

    pub fn tick(&self) {
        self.pos.inc(1);
    }

    /// Returns progress bar as string `[====>   ]`
    fn bar(fill_len: usize, total_len: usize) -> String {
        let fill_len = min(fill_len, total_len);
        format!(
            "[{}{}]",
            "▪".repeat(fill_len),
            " ".repeat(total_len - fill_len)
        )
    }
}

impl Display for Progress {
    #[allow(clippy::format_in_format_args)]
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        const WIDTH: usize = 60;
        let pos = self.pos.get();
        let text = match self.bound {
            ProgressBound::Count(count) => {
                let pos = min(count, pos);
                let ratio = pos as f32 / count as f32;
                let fill = (WIDTH as f32 * ratio) as usize;
                format!(
                    "{} {:>5.1}%      {:>28}",
                    Self::bar(fill, WIDTH),
                    100.0 * ratio,
                    format!("{pos}/{count}")
                )
            }
            ProgressBound::Duration(duration) => {
                let elapsed_secs = (Instant::now() - self.start_time).as_secs_f32();
                let duration_secs = duration.as_secs_f32();
                let ratio = 1.0_f32.min(elapsed_secs / duration_secs);
                let fill = (WIDTH as f32 * ratio) as usize;
                format!(
                    "{} {:>5.1}% {:>20} {:>12}",
                    Self::bar(fill, WIDTH),
                    100.0 * ratio,
                    format!("{elapsed_secs:.1}/{duration_secs:.0}s"),
                    pos
                )
            }
        };

        write!(
            f,
            "{:21}{}",
            style(&self.msg)
                .white()
                .bright()
                .bold()
                .on_color256(59)
                .for_stderr(),
            style(text).white().bright().on_color256(59).for_stderr()
        )
    }
}
