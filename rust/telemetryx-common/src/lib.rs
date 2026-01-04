/// TelemetryX Common - Shared domain types and utilities
///
/// This crate holds ergonomic, application-level types that represent events as
/// the ingestion service and other components expect to consume and process.
///
/// The implementation is split into modules to keep responsibilities clear:
/// - `adapters` : serde adapters (base64 bytes, etc.)
/// - `types` : domain Event and EventPayload
/// - `errors` : small error types used for validation
///
/// See `types` for usage examples and `errors` for validation semantics.
pub mod adapters;
pub mod errors;
pub mod types;

// re-export commonly used domain types at the crate root for convenience
pub use types::{Event, EventPayload};
