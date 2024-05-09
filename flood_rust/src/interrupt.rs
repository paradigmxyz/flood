use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

/// Notifies about received Ctrl-C signal
pub struct InterruptHandler {
    interrupted: Arc<AtomicBool>,
}

impl InterruptHandler {
    pub fn install() -> InterruptHandler {
        let cell = Arc::new(AtomicBool::new(false));
        let cell_ref = cell.clone();
        let _ = ctrlc::set_handler(move || cell_ref.store(true, Ordering::Relaxed));
        InterruptHandler { interrupted: cell }
    }

    /// Returns true if Ctrl-C was pressed
    pub fn is_interrupted(&self) -> bool {
        self.interrupted.load(Ordering::Relaxed)
    }
}
