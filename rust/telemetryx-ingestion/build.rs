fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Use a vendored protoc binary (protoc-bin-vendored) so CI doesn't need
    // an external protoc installed. Set PROTOC env var to the vendored binary.
    match protoc_bin_vendored::protoc_bin_path() {
        Ok(path) => std::env::set_var("PROTOC", path),
        Err(e) => eprintln!("warning: failed to locate vendored protoc: {}", e),
    }

    // Generate Rust types from proto for the ingestion crate.
    // We compile the proto located at repo root: ../../proto/events.proto
    tonic_build::configure()
        .build_server(false)
        .compile(&["../../proto/events.proto"], &["../../proto"])?;
    Ok(())
}
