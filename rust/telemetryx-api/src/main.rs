//! TelemetryX API Service
//!
//! REST + WebSocket API for querying analytics.
//! TODO: Implement your API logic here.

use std::env;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::from_default_env()
                .add_directive(tracing::Level::INFO.into()),
        )
        .init();

    let host = env::var("REST_HOST").unwrap_or_else(|_| "0.0.0.0".to_string());
    let port = env::var("REST_PORT").unwrap_or_else(|_| "8081".to_string());

    tracing::info!("TelemetryX API starting on {}:{}", host, port);
    tracing::info!("TODO: Implement REST API server");

    // TODO: Implement your server here
    // For now, just keep running
    loop {
        tokio::time::sleep(tokio::time::Duration::from_secs(60)).await;
    }
}
