# TelemetryX Python Brain - Development Commands
# ==============================================
# Usage: make <target>

.PHONY: proto install dev test lint format clean run

# Generate proto files
proto:
	python scripts/generate_proto.py

# Install dependencies
install:
	uv pip install -e .

# Install with dev dependencies
dev:
	uv pip install -e ".[dev]"

# Run tests
test:
	pytest

# Run tests with coverage
test-cov:
	pytest --cov=telemetryx --cov-report=html

# Lint code
lint:
	ruff check telemetryx
	mypy telemetryx

# Format code
format:
	ruff format telemetryx

# Clean generated files
clean:
	rm -rf telemetryx/proto/*_pb2*.py
	rm -rf .pytest_cache htmlcov .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Run the gRPC server
run:
	python -m telemetryx.grpc_server

# Regenerate protos and run
dev-run: proto run

