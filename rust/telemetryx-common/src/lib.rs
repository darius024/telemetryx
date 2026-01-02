//! TelemetryX Common - Shared types and utilities
//!
//! TODO: Add your shared types here

/// Placeholder module - implement your shared types
pub mod types {
    /// Example event type - replace with your implementation
    #[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
    pub struct Event {
        pub id: String,
        pub timestamp: i64,
        pub payload: serde_json::Value,
    }
}

#[cfg(test)]
mod tests {
    use super::types::Event;

    #[test]
    fn event_can_be_created() {
        let event = Event {
            id: "test-123".to_string(),
            timestamp: 1234567890,
            payload: serde_json::json!({"key": "value"}),
        };
        assert_eq!(event.id, "test-123");
        assert_eq!(event.timestamp, 1234567890);
    }
}
