use alloy_json_rpc::RpcError;
use alloy_transport::TransportErrorKind;

use err_derive::*;
use hdrhistogram::serialization::interval_log::IntervalLogWriterError;
use hdrhistogram::serialization::V2DeflateSerializeError;
use std::path::PathBuf;

#[derive(Debug, Error)]
pub enum FloodError {
    #[error(display = "Context data could not be serialized: {}", _0)]
    ContextDataEncode(#[source] rmp_serde::encode::Error),

    #[error(display = "Context data could not be deserialized: {}", _0)]
    ContextDataDecode(#[source] rmp_serde::decode::Error),

    #[error(display = "env var error: {}", _0)]
    EnvVar(#[source] std::env::VarError),

    #[error(display = "Failed to read file {:?}: {}", _0, _1)]
    ScriptRead(PathBuf, #[source] std::io::Error),

    #[error(display = "Failed to load script: {}", _0)]
    ScriptBuildError(#[source] rune::BuildError),

    #[error(display = "Failed to execute script function {}: {}", _0, _1)]
    ScriptExecError(String, rune::runtime::VmError),

    #[error(display = "Function {} returned error: {}", _0, _1)]
    FunctionResult(String, String),

    #[error(display = "{}", _0)]
    Diagnostics(#[source] rune::diagnostics::EmitError),

    #[error(display = "Failed to create output file {:?}: {}", _0, _1)]
    OutputFileCreate(PathBuf, std::io::Error),

    #[error(display = "Error writing HDR log: {}", _0)]
    HdrLogWrite(#[source] IntervalLogWriterError<V2DeflateSerializeError>),

    #[error(display = "Interrupted")]
    Interrupted,

    #[error(display = "Eth error: {}", _0)]
    Eth(#[source] RpcError<TransportErrorKind>),
}

pub type Result<T> = std::result::Result<T, FloodError>;
