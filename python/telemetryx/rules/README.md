# Rules Engine

Evaluates telemetry events against user-defined rules and triggers actions when conditions match.

## Overview

```
Event ──▶ Repository ──▶ Evaluator ──▶ Actions
              │
              ▼
          Redis Cache
```

1. **Repository** loads rules from PostgreSQL, caches in Redis
2. **Evaluator** checks event against each rule's condition (DSL)
3. **Actions** execute when a rule matches (log, alert, webhook)

## Data Model

### Rule

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier |
| `name` | string | Human-readable name |
| `description` | string | What this rule detects |
| `enabled` | bool | Can be toggled off |
| `priority` | int | Evaluation order (lower = first) |
| `severity` | enum | INFO, WARNING, ERROR, CRITICAL |
| `condition` | object | When to trigger (DSL) |
| `actions` | list | What to do when triggered |

### Condition DSL

JSON-logic inspired syntax:

```json
{"field": "value", "op": ">", "value": 100}
```

```json
{
  "and": [
    {"field": "event_type", "op": "==", "value": "error"},
    {"field": "value", "op": ">", "value": 50}
  ]
}
```

### Operators

| Operator | Description |
|----------|-------------|
| `==`, `!=` | Equality |
| `>`, `>=`, `<`, `<=` | Comparison |
| `contains`, `startswith`, `endswith` | String matching |
| `regex` | Regular expression |
| `in` | Value in list |

### Actions

| Type | Description |
|------|-------------|
| `log` | Write to structured log |
| `alert` | Create alert record |
| `webhook` | HTTP POST to URL |

## Module Structure

```
rules/
├── models.py      # Pydantic models (Rule, Condition, Action)
├── dsl.py         # DSL parser and condition evaluation
├── engine.py      # RulesEngine - orchestrates evaluation
├── repository.py  # PostgreSQL CRUD + Redis caching
└── actions.py     # Action executors
```

## Database Schema

```sql
CREATE TABLE rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    enabled BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 100,
    severity VARCHAR(20) DEFAULT 'INFO',
    condition JSONB NOT NULL,
    actions JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Redis Caching

| Key | TTL | Purpose |
|-----|-----|---------|
| `rules:all` | 60s | Enabled rule IDs |
| `rules:id:{uuid}` | 300s | Individual rule |

