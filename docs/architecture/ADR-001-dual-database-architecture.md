# ADR-001: Dual Database Architecture (SQLAlchemy + asyncpg)

**Status:** Accepted
**Date:** 2026-03-25
**Context:** Backend audit identified potential confusion around two database access layers

## Decision

UATP Capsule Engine uses two database access layers concurrently:

1. **SQLAlchemy (async)** - Primary ORM layer for models, migrations, and complex queries
2. **asyncpg** - High-performance raw query layer for performance-critical paths

## Context

During development, we found that certain operations required:
- ORM capabilities for model relationships, schema migrations, and maintainability
- Raw query performance for high-throughput capsule operations

Rather than compromise on either requirement, we implemented both layers.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Application Layer                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────┐      ┌──────────────────────┐        │
│  │   SQLAlchemy (db)    │      │  asyncpg (db_manager) │        │
│  │                      │      │                      │        │
│  │  • ORM Models        │      │  • Raw SQL queries   │        │
│  │  • Migrations        │      │  • Bulk operations   │        │
│  │  • Relationships     │      │  • Connection pool   │        │
│  │  • Complex queries   │      │  • High throughput   │        │
│  │                      │      │                      │        │
│  │  src/core/database.py│      │  src/database/       │        │
│  │                      │      │  connection.py       │        │
│  └──────────┬───────────┘      └──────────┬───────────┘        │
│             │                              │                    │
│             ▼                              ▼                    │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    PostgreSQL / SQLite                      ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## When to Use Each Layer

### Use SQLAlchemy (`src/core/database.db`) for:

```python
from src.core.database import db

async with db.get_session() as session:
    # ORM queries - relationships, complex joins
    capsule = await session.get(CapsuleModel, capsule_id)

    # Model operations
    session.add(new_model)
    await session.commit()
```

- Creating, updating, deleting models
- Queries involving relationships
- Migrations and schema changes
- Complex queries with joins
- Any operation where maintainability > raw performance

### Use asyncpg (`src/database/connection.py`) for:

```python
from src.database.connection import get_database_manager

db_manager = get_database_manager()
async with db_manager.get_connection() as conn:
    # Raw SQL for performance-critical paths
    results = await conn.fetch(
        "SELECT * FROM capsules WHERE timestamp > $1",
        cutoff_time
    )
```

- High-throughput read operations
- Bulk inserts (using `copy_to_table`)
- Performance-critical paths where ORM overhead matters
- Simple queries that don't need relationship loading

## Initialization

Both layers are initialized in `src/app_factory.py`:

```python
# SQLAlchemy is always initialized
db.init_app(app)

# asyncpg is optional (PostgreSQL only, fails gracefully with SQLite)
try:
    await db_manager.connect()
except Exception:
    logger.warning("PostgreSQL not available (using SQLite)")
```

## Development vs Production

| Environment | SQLAlchemy | asyncpg |
|-------------|------------|---------|
| Development | SQLite | Not initialized |
| Production | PostgreSQL | PostgreSQL (same DB) |

## Trade-offs

### Pros
- Best of both worlds: ORM convenience + raw performance
- Clear separation of concerns
- Graceful degradation in development

### Cons
- Two mental models for database access
- Must keep both layers in sync during schema changes
- Potential for confusion in code reviews

## Guidelines

1. **Default to SQLAlchemy** unless you have a measured performance need
2. **Document why** when using asyncpg in new code
3. **Keep schema changes** in SQLAlchemy migrations only
4. **Health checks** should verify both layers in production

## Related Files

- `src/core/database.py` - SQLAlchemy async setup
- `src/database/connection.py` - asyncpg connection manager
- `src/app_factory.py:104-128` - Initialization logic
- `src/observability/health_checks.py` - Health checks for both layers

## Alternatives Considered

1. **SQLAlchemy only**: Would sacrifice performance on critical paths
2. **asyncpg only**: Would lose ORM benefits, harder to maintain
3. **Different ORM (Tortoise, SQLModel)**: Would require rewrite, unproven at scale

## Consequences

- Engineers must understand when to use each layer
- Code reviews should verify appropriate layer choice
- Both layers must be tested independently
