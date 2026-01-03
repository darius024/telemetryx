fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Generate Rust types from proto for the ingestion crate.
    // We compile the proto located at repo root: ../../proto/events.proto
    tonic_build::configure()
        .build_server(false)
        .compile(&["../../proto/events.proto"], &["../../proto"])?;
    Ok(())
}
