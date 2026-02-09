# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NSoT (Network Source of Truth) is a Django/DRF-based network asset management and IP address management (IPAM) platform. It provides an API-first approach for tracking network entities (devices, networks/subnets, interfaces, circuits, protocols) organized under Sites as namespace boundaries.

## Common Commands

### Install dependencies
```bash
uv sync --all-extras
```

### Run tests
```bash
NSOT_API_VERSION=1.0 uv run pytest -vv tests/
```

### Run a single test file
```bash
NSOT_API_VERSION=1.0 uv run pytest -vv tests/api_tests/test_networks.py
```

### Run a single test
```bash
NSOT_API_VERSION=1.0 uv run pytest -vv tests/api_tests/test_networks.py::TestNetwork::test_name
```

### Lint
```bash
uv run ruff check nsot/ tests/
```

### Format check
```bash
uv run ruff format --check nsot/ tests/
```

### Format code
```bash
uv run ruff format nsot/ tests/
```

### Build package
```bash
uv build
```

### Run dev server
```bash
uv run nsot-server start
```

### Initialize server config
```bash
uv run nsot-server init
```

## Important Notes

- The `NSOT_API_VERSION=1.0` environment variable is **required** when running tests.
- Test settings are in `tests/test_settings.py` (uses SQLite). The pytest Django settings module is configured in `pyproject.toml`.
- Ruff is configured with `line-length = 79` and excludes `nsot/vendor` and `nsot/migrations`.
- Set `NSOT_DEBUG=1` to enable debug logging in tests.

## Architecture

### Resource Model Hierarchy

All manageable entities inherit from `Resource` (abstract base model in `nsot/models/resource.py`), which provides:
- A flexible attribute system via the `Attribute`/`Value` models (arbitrary key-value metadata on any resource)
- `ResourceSetTheoryQuerySet` enabling set-theory queries on attributes (e.g., `owner=jathan +metro=lax` for union, `-` for difference, default is intersection, `_regex` suffix for pattern matching)
- A `post_delete` signal that cascades deletion of attribute Values when a Resource is deleted

Resource subclasses: `Network`, `Device`, `Interface`, `Circuit`, `Protocol`.

### Site as Namespace

All resources belong to a `Site`. The API supports both top-level access (`/api/devices/`) and site-scoped access (`/api/sites/<id>/devices/`) via nested routers (`BulkRouter` + `BulkNestedRouter` in `nsot/api/routers.py`).

### API Layer (`nsot/api/`)

- **ViewSets** (`views.py`): Extend `BaseNsotViewSet` which builds on DRF's `ReadOnlyModelViewSet`. Supports bulk create/update/delete via vendored `djangorestframework-bulk` (`nsot/vendor/`).
- **Serializers** (`serializers.py`): Custom fields include `JSONDictField`, `JSONListField`, `MACAddressField`, and `NaturalKeyRelatedField` (accepts PK or natural key).
- **Routers** (`routers.py`): Custom `BulkRouter` and `BulkNestedRouter` for nested site resources.
- **Auth** (`auth.py`): Multiple authentication backends — `AuthTokenAuthentication` (email:token), `EmailHeaderAuthentication` (reverse proxy header `X-NSoT-Email`), plus DRF's Basic and Session auth.
- **Versioning**: Uses DRF's `AcceptHeaderVersioning`.

### URL Structure (`nsot/conf/urls.py`)

- `/api/` — REST API (registered in `nsot/api/urls.py`)
- `/admin/` — Django admin
- `/schema.json` — OpenAPI schema
- All other URLs fall through to the AngularJS frontend (`FeView`)

### Frontend

AngularJS 1.3 + Bootstrap 3 single-page app. Built with Gulp (`gulpfile.js`). Static assets in `nsot/static/`. Templates use Jinja2.

### Configuration

Server config is managed via logan runner. User config lives at `~/.nsot/nsot.conf.py` (override with `NSOT_CONF` env var). Django settings base is `nsot/conf/settings.py`.

### Test Structure

- `tests/api_tests/` — Integration tests against REST API endpoints
- `tests/model_tests/` — Unit tests for Django models
- Both directories have their own `fixtures.py` (re-exported via `conftest.py`) and `util.py` with test helpers

## Development Workflow

- Use **git worktrees** for feature branches to keep the main checkout clean:
  ```bash
  git worktree add ~/sandbox/src/nsot-<feature> -b <feature-branch> main
  ```
- Use parallel sub-agents for independent tasks within a plan.
- Always run tests and lint before committing (see Common Commands above).
