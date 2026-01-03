<div align="center">

# 🐍 TelemetryX Python Brain

**The Smart Layer — Rules Engine, ML, and Data Pipelines**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![gRPC](https://img.shields.io/badge/gRPC-244c5a?style=for-the-badge&logo=google&logoColor=white)](https://grpc.io/)
[![Polars](https://img.shields.io/badge/Polars-CD792C?style=for-the-badge&logo=polars&logoColor=white)](https://pola.rs/)

*Business logic and ML where flexibility matters.*

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Learning Goals](#-learning-goals)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Implementation Roadmap](#-implementation-roadmap)
- [Setup & Development](#-setup--development)
- [Testing](#-testing)

---

## 🎯 Overview

The Python Brain is the **intelligent control plane** of TelemetryX. While Rust handles the high-throughput data plane (100K+ events/sec), Python provides:

| Capability | Description |
|------------|-------------|
| **Rules Engine** | Configurable business logic for event evaluation and alerting |
| **Anomaly Detection** | ML-based outlier detection on telemetry streams |
| **Data Pipelines** | Batch analysis, reporting, and ETL workflows |
| **gRPC Server** | Service interface exposing Python capabilities to Rust |

### Design Philosophy

```
┌─────────────────────────────────────────────────────────────┐
│                    TELEMETRYX PHILOSOPHY                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   🦀 RUST = Speed        │   🐍 PYTHON = Flexibility        │
│   ──────────────────     │   ────────────────────────       │
│   • Hot path             │   • Business logic               │
│   • 100K events/sec      │   • Configurable rules           │
│   • Sub-ms latency       │   • ML inference                 │
│   • Memory efficiency    │   • Rapid iteration              │
│                          │   • Rich ecosystem               │
│                                                              │
│   Speed where it matters. Flexibility where it counts.      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Architecture

### System Context

```
                              ┌─────────────────────────────────────┐
                              │         RUST CORE                   │
                              │                                     │
 Events ──────────────────────▶  Ingestion ──▶ Processor ──▶ Router │
 (Logs, Metrics, Actions)     │                              │      │
                              │                              │      │
                              └──────────────────────────────┼──────┘
                                                             │
                                                             │ gRPC
                                                             │ Protocol Buffers
                                                             ▼
                              ┌─────────────────────────────────────┐
                              │         PYTHON BRAIN                │
                              │                                     │
                              │  ┌─────────┐  ┌─────────┐  ┌─────┐ │
                              │  │  Rules  │  │   ML    │  │ ETL │ │
                              │  │ Engine  │  │ Models  │  │     │ │
                              │  └────┬────┘  └────┬────┘  └──┬──┘ │
                              │       │            │          │    │
                              │       └────────────┴──────────┘    │
                              │                    │               │
                              └────────────────────┼───────────────┘
                                                   │
                              ┌────────────────────┴───────────────┐
                              │                                     │
                              ▼                                     ▼
                         ┌─────────┐                          ┌─────────┐
                         │ Postgres│                          │  Redis  │
                         │ (Store) │                          │ (Cache) │
                         └─────────┘                          └─────────┘
```

### Internal Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                           PYTHON BRAIN                                  │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      gRPC SERVER (Port 50051)                    │   │
│  │                                                                  │   │
│  │  • Async server using grpcio + asyncio                          │   │
│  │  • Handles concurrent requests from Rust services               │   │
│  │  • Graceful shutdown, health checks                             │   │
│  │                                                                  │   │
│  └──────────────────────────────┬──────────────────────────────────┘   │
│                                 │                                       │
│         ┌───────────────────────┼───────────────────────┐              │
│         │                       │                       │              │
│         ▼                       ▼                       ▼              │
│  ┌─────────────┐        ┌─────────────┐        ┌─────────────┐        │
│  │   RULES     │        │   ANOMALY   │        │    DATA     │        │
│  │   ENGINE    │        │  DETECTION  │        │  PIPELINES  │        │
│  │             │        │             │        │             │        │
│  │ • DSL Parser│        │ • Isolation │        │ • Polars    │        │
│  │ • Evaluator │        │   Forest    │        │ • Batch ETL │        │
│  │ • Actions   │        │ • Z-Score   │        │ • Reports   │        │
│  │ • Alerts    │        │ • ARIMA     │        │ • Exports   │        │
│  └──────┬──────┘        └──────┬──────┘        └──────┬──────┘        │
│         │                      │                      │               │
│         └──────────────────────┴──────────────────────┘               │
│                                │                                       │
│                    ┌───────────┴───────────┐                          │
│                    │   SHARED SERVICES     │                          │
│                    │                       │                          │
│                    │  • PostgreSQL Client  │                          │
│                    │  • Redis Client       │                          │
│                    │  • Logging (structlog)│                          │
│                    │  • Config Management  │                          │
│                    └───────────────────────┘                          │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Rust ↔ Python Communication

The Rust API service connects to Python Brain via gRPC on port 50051:

```
┌─────────────────────┐         ┌─────────────────────┐
│    Rust API         │         │   Python Brain      │
│    (port 8081)      │         │   (port 50051)      │
│                     │         │                     │
│  ┌───────────────┐  │  gRPC   │  ┌───────────────┐  │
│  │ tonic client  │──┼─────────┼─▶│ grpcio server │  │
│  └───────────────┘  │         │  └───────────────┘  │
│                     │         │                     │
└─────────────────────┘         └─────────────────────┘
```

Both services share `.proto` definitions in the `proto/` directory.

---

## 🎓 Learning Goals

Building the Python Brain teaches **production-grade Python engineering**:

### Core Skills

| Skill | Description | Where Applied |
|-------|-------------|---------------|
| **asyncio Mastery** | Event loops, coroutines, concurrent tasks | gRPC server, async handlers |
| **Type Safety** | Type hints, Pydantic models, mypy strict mode | All modules |
| **Structured Logging** | Context-rich, machine-parseable logs | structlog throughout |
| **Configuration Management** | Environment-based config, secrets handling | Pydantic Settings |

### Production Patterns

| Pattern | Description | Where Applied |
|---------|-------------|---------------|
| **Graceful Shutdown** | Handle SIGTERM, drain connections | gRPC server lifecycle |
| **Health Checks** | Liveness/readiness probes | Docker health checks |
| **Circuit Breakers** | Fail fast on downstream issues | Database/Redis clients |
| **Retry Logic** | Exponential backoff with jitter | External service calls |

### gRPC & Service Design

| Concept | Description | Where Applied |
|---------|-------------|---------------|
| **Protocol Buffers** | Schema design, versioning, evolution | `proto/` definitions |
| **Unary RPC** | Request-response pattern | Rule evaluation |
| **Server Streaming** | Push multiple responses | Batch analysis results |
| **Bidirectional Streaming** | Real-time interaction | Live anomaly detection |
| **Error Propagation** | Status codes, error details | Cross-service boundaries |

### Machine Learning & Data Engineering

| Concept | Description | Where Applied |
|---------|-------------|---------------|
| **Model Serving** | Load, cache, and serve trained models | Anomaly detection |
| **Feature Engineering** | Transform raw events to features | ML preprocessing |
| **Polars DataFrames** | Fast columnar data processing | Analysis pipelines |
| **Redis Patterns** | Caching, counters, pub/sub | Real-time state |

---

## 🛠️ Tech Stack

### Core Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `grpcio` | ≥1.60.0 | gRPC server framework |
| `grpcio-tools` | ≥1.60.0 | Protocol buffer compilation |
| `pydantic` | ≥2.0.0 | Data validation and settings |
| `structlog` | ≥24.0.0 | Structured logging |
| `redis` | ≥5.0.0 | Redis client (async support) |
| `psycopg[binary]` | ≥3.1.0 | PostgreSQL driver (async) |
| `polars` | ≥0.20.0 | Fast DataFrame library |

### Development Tools

| Tool | Purpose |
|------|---------|
| `pytest` + `pytest-asyncio` | Testing framework with async support |
| `ruff` | Fast Python linter and formatter |
| `mypy` | Static type checking |

---

## 📁 Project Structure

```
python/
├── pyproject.toml              # Project configuration & dependencies
├── README.md                   # This file
│
├── telemetryx/                 # Main package
│   ├── __init__.py             # Package version
│   │
│   ├── grpc_server/            # gRPC Service Layer
│   │   ├── __init__.py
│   │   ├── __main__.py         # Entry point: python -m telemetryx.grpc_server
│   │   ├── server.py           # Async gRPC server setup
│   │   ├── handlers.py         # RPC method implementations
│   │   └── interceptors.py     # Logging, auth, metrics interceptors
│   │
│   ├── rules/                  # Rules Engine
│   │   ├── __init__.py
│   │   ├── engine.py           # Core evaluation engine
│   │   ├── dsl.py              # Rule DSL parser (JSON-logic style)
│   │   ├── models.py           # Rule data models (Pydantic)
│   │   ├── actions.py          # Alert/webhook/notification actions
│   │   └── repository.py       # Rule storage (PostgreSQL)
│   │
│   ├── ml/                     # Machine Learning
│   │   ├── __init__.py
│   │   ├── anomaly.py          # Anomaly detection algorithms
│   │   ├── features.py         # Feature extraction from events
│   │   ├── registry.py         # Model loading and caching
│   │   └── models/             # Serialized model files
│   │
│   ├── pipelines/              # Data Pipelines
│   │   ├── __init__.py
│   │   ├── analysis.py         # Aggregation and analysis workflows
│   │   └── export.py           # Data export utilities
│   │
│   ├── db/                     # Database Layer
│   │   ├── __init__.py
│   │   ├── postgres.py         # PostgreSQL connection pool
│   │   └── redis.py            # Redis client wrapper
│   │
│   ├── core/                   # Shared Utilities
│   │   ├── __init__.py
│   │   ├── config.py           # Configuration (Pydantic Settings)
│   │   ├── logging.py          # Structured logging setup
│   │   └── exceptions.py       # Custom exception hierarchy
│   │
│   └── proto/                  # Generated protobuf code
│       └── (generated files)
│
└── tests/                      # Test Suite
    ├── __init__.py
    ├── conftest.py             # Shared fixtures
    └── test_*.py               # Test modules
```

---

## 🗺️ Implementation Roadmap

### Phase 1: Foundation

- [ ] **Proto Schema Design**
  - [ ] Define `Event` message types
  - [ ] Define `RulesService` (Evaluate, CreateRule, UpdateRule, DeleteRule)
  - [ ] Define `AnalyticsService` (DetectAnomalies, Analyze)
  - [ ] Generate Python stubs

- [ ] **Core Infrastructure**
  - [ ] Configuration management with Pydantic Settings
  - [ ] Structured logging setup
  - [ ] Exception hierarchy

### Phase 2: gRPC Server

- [ ] **Server Implementation**
  - [ ] Async gRPC server with proper lifecycle
  - [ ] Health check endpoint
  - [ ] Graceful shutdown handling
  - [ ] Request logging interceptor

- [ ] **Database Connections**
  - [ ] PostgreSQL connection pool (psycopg)
  - [ ] Redis client with connection pooling

### Phase 3: Rules Engine

- [ ] **Rule Data Model**
  - [ ] Pydantic models for rules
  - [ ] PostgreSQL schema and repository
  - [ ] Rule caching in Redis

- [ ] **DSL & Evaluation**
  - [ ] JSON-logic style condition parser
  - [ ] Comparison operators (>, <, ==, etc.)
  - [ ] Logical operators (and, or, not)
  - [ ] Window state management (Redis)
  - [ ] Action execution framework

### Phase 4: Anomaly Detection

- [ ] **Statistical Methods**
  - [ ] Z-score based detection
  - [ ] Moving average with deviation threshold

- [ ] **ML Models**
  - [ ] Isolation Forest implementation
  - [ ] Feature extraction pipeline
  - [ ] Model registry and caching

### Phase 5: Data Pipelines

- [ ] **Analysis & Export**
  - [ ] Polars-based aggregations
  - [ ] Time-series windowing
  - [ ] CSV/Parquet export

---

## 🚀 Setup & Development

### Prerequisites

- Python 3.11+
- Docker (for PostgreSQL and Redis)
- protoc (Protocol Buffer compiler)

### Installation

```bash
# From repository root
cd python

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install in development mode
pip install -e ".[dev]"
```

### Start Infrastructure

```bash
# From repository root
docker compose -f infra/docker-compose.yml up -d
```

### Generate Proto Stubs

```bash
# From repository root
python -m grpc_tools.protoc \
    -I proto \
    --python_out=python/telemetryx/proto \
    --grpc_python_out=python/telemetryx/proto \
    proto/*.proto
```

### Run the Server

```bash
python -m telemetryx.grpc_server
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GRPC_HOST` | `0.0.0.0` | gRPC server bind address |
| `GRPC_PORT` | `50051` | gRPC server port |
| `DATABASE_URL` | - | PostgreSQL connection string |
| `REDIS_URL` | - | Redis connection string |
| `PYTHON_ENV` | `development` | Environment (development/staging/production) |
| `LOG_LEVEL` | `INFO` | Logging level |

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=telemetryx --cov-report=html

# Type checking
mypy telemetryx

# Linting and formatting
ruff check telemetryx
ruff format telemetryx
```

---

<div align="center">

**Part of TelemetryX — Real-Time Analytics Platform**

*🦀 Rust Core × 🐍 Python Brain*

</div>
