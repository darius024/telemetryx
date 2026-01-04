# TelemetryX — Ingestion FEATURES

This document captures the high-level features and acceptance criteria for the Rust ingestion service (`telemetryx-ingestion`). Use this as the canonical checklist for design, implementation, and testing decisions.

1. High-level purpose
- Accept high-rate events from producers (HTTP and optional TCP) and reliably forward them to downstream systems for processing and storage.

2. Core responsibilities
- Ingest: accept events via HTTP POST (/ingest) and optionally via framed TCP.
- Validate & normalize: decode wire format (JSON or Protobuf), validate required fields, normalize timestamps and utf-8 fields.
- Buffer & backpressure: enqueue events on a bounded, async queue and apply backpressure if internal queues are full.
- Preprocess: perform fast, CPU-cheap transforms (timestamp normalization, light enrichment, schema migration) in a worker pool.
- Route: fan-out or forward events to configurable destinations (Postgres for persistence, Redis for counters/pubsub, Python brain via gRPC). Support retry/backoff.
- Observability: emit structured logs, tracing spans, and Prometheus metrics; expose /metrics endpoint.
- Health & lifecycle: expose `/health` for liveness/ready checks and support graceful shutdown (SIGINT/SIGTERM) with task coordination and flush.

3. Acceptance criteria (ready-to-ship)
- The service compiles and passes unit and integration tests.
- `/health` returns healthy when listening and able to accept requests.
- Ingestion endpoints accept sample events and respond 2xx; decoded events map to `Event` domain type.
- Backpressure behavior: when queue is full, producers receive a clear failure code (429 or configured) and the service does not OOM.
- Observability: basic Prometheus metrics are exposed (ingest_rate, processing_latency_histogram, queue_depth), and `tracing` spans are present for request lifecycle.
- Graceful shutdown: on SIGTERM the service stops accepting new connections, flushes workers for a configurable timeout, then exits.

4. API surface (minimal)
- GET /health — returns 200 OK when the service is accepting requests and can reach required subsystems (optional checks).
- POST /ingest — accepts one or more events (JSON or Protobuf). Returns 202 Accepted or 200 OK on success. Returns 4xx on invalid payload and 429 when under backpressure.
- GET /metrics — Prometheus metrics endpoint.

5. Observability & metrics (required)
- Tracing: per-request spans with fields: request_id, source_ip, payload_size, decode_time, enqueue_time, process_time.
- Metrics (Prometheus):
  - ingestion_requests_total (counter)
  - ingestion_requests_errors_total (counter)
  - ingestion_queue_depth (gauge)
  - ingestion_processing_latency_seconds (histogram)
  - ingestion_dropped_total (counter)

6. Reliability & error handling
- Use structured, typed errors (`thiserror`) and map to appropriate HTTP codes.
- Retry policies for downstream writes (configurable max attempts and backoff).
- Circuit-breaker or fail-fast for downstream outages to protect ingestion throughput.

7. Performance & scalability
- Target per-instance throughput: configurable; design for horizontal scaling (stateless ingestion where possible).
- Use bounded async queues (`tokio::sync::mpsc::channel(bound)`) initially; measure and optimize hot-paths after profiling.
- Avoid blocking operations on the hot path; use background tasks for IO-heavy work.

8. Security
- Validate and sanitize incoming payloads; enforce size limits and rate limiting per source.
- Use TLS for HTTP and optional mutual TLS for gRPC where needed (left for infra config).

9. Deployment & operational notes
- Docker image must include a HEALTHCHECK that queries `/health`.
- CI should run `cargo fmt`, `cargo clippy`, and `cargo test` for the ingestion crate on each PR.
- Provide runbook entries for: handling queue saturation, downstream DB outages, and verifying metrics/tracing.

10. Quick dev/run commands
```bash
# from repo root
cd rust/telemetryx-ingestion
cargo run --release -- --config ./config/dev.yaml
# then
curl -X POST http://127.0.0.1:8080/ingest -d '{"events":[{"id":"1","ts":"2025-01-01T00:00:00Z","payload":{}}]}' -H 'Content-Type: application/json'
```
---