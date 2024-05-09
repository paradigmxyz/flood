use std::collections::{HashMap, HashSet};
use std::sync::Arc;
use std::time::{Duration, Instant};

use alloy_json_rpc::{Request, RpcError, RpcReturn};
use alloy_primitives::U64;
use alloy_rpc_client::RpcClient;
use alloy_transport_http::Http;
use hdrhistogram::Histogram;
use rune::runtime::{Object, Shared};
use rune::{Any, Value};
use serde_json::value::RawValue;
use std::fmt::Debug;
use try_lock::TryLock;

use crate::FloodError;

pub struct NodeInfo {
    pub chain_id: U64,
}

#[derive(Clone, Debug)]
pub struct SessionStats {
    pub req_count: u64,
    pub req_succ_count: u64,
    pub req_errors: HashSet<String>,
    pub req_error_count: u64,
    pub queue_length: u64,
    pub mean_queue_length: f32,
    pub resp_times_ns: Histogram<u64>,
}

impl SessionStats {
    pub fn new() -> SessionStats {
        Default::default()
    }

    pub fn start_request(&mut self) -> Instant {
        if self.req_count > 0 {
            self.mean_queue_length +=
                (self.queue_length as f32 - self.mean_queue_length) / self.req_count as f32;
        }
        self.queue_length += 1;
        Instant::now()
    }

    pub fn complete_request<Resp, E>(&mut self, duration: Duration, rs: &Result<Resp, RpcError<E>>)
    where
        E: Debug,
        Resp: RpcReturn,
    {
        self.queue_length -= 1;
        let duration_ns = duration.as_nanos().clamp(1, u64::MAX as u128) as u64;
        self.resp_times_ns.record(duration_ns).unwrap();
        self.req_count += 1;
        match rs {
            // If call successful increment row count => call_count
            Ok(_) => self.req_succ_count += 1,
            Err(e) => {
                self.req_error_count += 1;
                self.req_errors.insert(format!("{:?}", e));
            }
        }
    }

    /// Resets all accumulators
    pub fn reset(&mut self) {
        self.req_error_count = 0;
        self.req_succ_count = 0;
        self.mean_queue_length = 0.0;
        self.req_errors.clear();
        self.resp_times_ns.clear();

        // note that current queue_length is *not* reset to zero because there
        // might be pending requests and if we set it to zero, that would underflow
    }
}

impl Default for SessionStats {
    fn default() -> Self {
        SessionStats {
            req_count: 0,
            req_succ_count: 0,
            req_errors: HashSet::new(),
            req_error_count: 0,
            queue_length: 0,
            mean_queue_length: 0.0,
            resp_times_ns: Histogram::new(3).unwrap(),
        }
    }
}

/// This is the main object that a workload script uses to interface with the outside world.
/// It also tracks query execution metrics such as number of requests, rows, response times etc.
#[derive(Any)]
pub struct Context {
    pub session: Arc<RpcClient<Http<reqwest::Client>>>,
    statements: HashMap<String, Arc<Request<Box<RawValue>>>>,
    pub stats: TryLock<SessionStats>,
    #[rune(get, set, add_assign, copy)]
    pub load_cycle_count: u64,
    #[rune(get)]
    pub data: Value,
}

// Needed, because Rune `Value` is !Send, as it may contain some internal pointers.
// Therefore it is not safe to pass a `Value` to another thread by cloning it, because
// both objects could accidentally share some unprotected, `!Sync` data.
// To make it safe, the same `Context` is never used by more than one thread at once and
// we make sure in `clone` to make a deep copy of the `data` field by serializing
// and deserializing it, so no pointers could get through.
unsafe impl Send for Context {}
unsafe impl Sync for Context {}

impl Context {
    pub fn new(session: RpcClient<Http<reqwest::Client>>) -> Context {
        Context {
            session: Arc::new(session),
            statements: HashMap::new(),
            stats: TryLock::new(SessionStats::new()),
            load_cycle_count: 0,
            data: Value::Object(Shared::new(Object::new())),
        }
    }

    /// Clones the context for use by another thread.
    /// The new clone gets fresh statistics.
    /// The user data gets passed through serialization and deserialization to avoid
    /// accidental data sharing.
    pub fn clone(&self) -> Result<Self, FloodError> {
        let serialized = rmp_serde::to_vec(&self.data)?;
        let deserialized: Value = rmp_serde::from_slice(&serialized)?;
        Ok(Context {
            session: self.session.clone(),
            statements: self.statements.clone(),
            stats: TryLock::new(SessionStats::default()),
            load_cycle_count: self.load_cycle_count,
            data: deserialized,
        })
    }

    /// Returns node metadata such as node name and node version.
    pub async fn node_info<E>(&self) -> Result<Option<NodeInfo>, RpcError<E>> {
        let request = self.session.request("eth_chainId", ());
        let res = request.await;
        if let Ok(chain_id) = res {
            return Ok(Some(NodeInfo { chain_id }));
        }
        Ok(None)
    }

    /// Returns the current accumulated request stats snapshot and resets the stats.
    pub fn take_session_stats(&self) -> SessionStats {
        let mut stats = self.stats.try_lock().unwrap();
        let result = stats.clone();
        stats.reset();
        result
    }

    /// Resets query and request counters
    pub fn reset_session_stats(&self) {
        self.stats.try_lock().unwrap().reset();
    }
}
