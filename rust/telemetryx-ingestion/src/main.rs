//! TelemetryX Ingestion Service
//! 
//! High-performance event ingestion service.
//! TODO: Implement your ingestion logic here.

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

    let host = env::var("SERVER_HOST").unwrap_or_else(|_| "0.0.0.0".to_string());
    let port = env::var("SERVER_PORT").unwrap_or_else(|_| "8080".to_string());

    tracing::info!("TelemetryX Ingestion starting on {}:{}", host, port);
    tracing::info!("TODO: Implement ingestion server");

    // TODO: Implement your server here
    // For now, just keep running
    loop {
        tokio::time::sleep(tokio::time::Duration::from_secs(60)).await;
    }
}

