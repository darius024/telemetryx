# telemetryx — Rust Ingestion TODOs

This README is focused solely on the Rust ingestion work (the `telemetryx-ingestion` crate).

How to use
- Check items locally by replacing `[ ]` with `[x]` and push changes.

Guiding principles
- Keep the ingestion binary small and fast. Put reusable types and validation in `telemetryx-common`.
- Avoid unnecessary allocations and copies in the hot path. Prefer zero-copy parsing and bounded queues.

## Ingestion-focused TODO

1. [ ] Define protobuf contract for ingestion (`proto/events.proto`)
   - Acceptance: `events.proto` finalized for ingestion needs, Rust code generated with `prost`/`tonic` (or chosen codegen), and a small compile test.

2. [ ] Shared types & validation (`telemetryx-common`)
   - Acceptance: `Event` and related types implemented with `serde`, validation helpers, and unit tests for parsing and invalid inputs.

3. [ ] Centralized configuration for ingestion
   - Acceptance: `Config` struct implemented (env + file support), defaults documented, and wired into `telemetryx-ingestion`.

4. [ ] Ingestion service (TCP/HTTP) basic server
   - Acceptance: `telemetryx-ingestion` accepts HTTP and/or TCP, decodes events into `Event`, responds with 2xx, supports graceful shutdown and exposes `/health`.

5. [ ] Ring buffer & backpressure
   - Acceptance: Bounded queue/ring-buffer with backpressure semantics (or proven crate integration), tests showing behavior under overload.

6. [ ] Lightweight stream preprocessing inside ingestion
   - Acceptance: Minimal batching/windowing/rate-limiting implemented where necessary; unit tests and a small integration test with the server.

7. [ ] Output router (fan-out from ingestion)
   - Acceptance: Router forwards events to configured destinations (Postgres, Redis, Python gRPC) with retry/backoff and configurable destinations.

8. [ ] Observability, errors & metrics (ingestion)
   - Acceptance: `tracing` instrumentation in hot paths, Prometheus metrics endpoint (queue depth, event rate, latencies), and `thiserror`-based errors logged with context.

9. [ ] Tests, benchmarks & profiling (ingestion hot paths)
   - Acceptance: Unit and integration tests, `criterion` benchmarks for hot code paths, and instructions to produce flamegraphs / use `tokio-console`.

10. [ ] CI & Docker for ingestion
    - Acceptance: CI runs `cargo fmt`, `cargo clippy`, `cargo test` for ingestion; Dockerfile builds a multi-stage image with a healthcheck pointing at `/health`.

## Quick commands (ingestion)

Build ingestion crate (release):
```bash
cd rust/telemetryx-ingestion
cargo build --release
```

Run ingestion tests:
```bash
cd rust/telemetryx-ingestion
cargo test
```

Generate Rust protobuf code (example using prost-build in a build script is recommended):
```bash
protoc --rust_out=./rust/telemetryx-proto --proto_path=./proto ./proto/events.proto
```

Dev: run with tokio-console & metrics (example env):
```bash
RUST_LOG=info TOKIO_CONSOLE=1 cargo run -p telemetryx-ingestion
```

---
