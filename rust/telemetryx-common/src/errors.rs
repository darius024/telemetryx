// errors.rs - centralized error types for telemetryx-common
use thiserror::Error;

/// Errors produced during event validation and parsing.
#[derive(Error, Debug)]
pub enum EventError {
    /// The event is missing an identifier.
    #[error("missing event id")]
    MissingId,

    /// The event timestamp appears to be in the future beyond allowed skew.
    #[error("event timestamp is in the future")]
    TimestampInFuture,

    /// Generic payload parse error, contains a short message.
    #[error("payload parse error: {0}")]
    PayloadParse(String),
}
