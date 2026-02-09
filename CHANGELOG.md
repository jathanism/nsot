# CHANGELOG


## v2.0.4 (2026-02-09)

### Bug Fixes

- Fall back to NSOT_PORT when address has no port
  ([`1402939`](https://github.com/jathanism/nsot/commit/1402939b0ea0f188263ba763425368d3642d5e3f))

When --address is given without a :port suffix (e.g. "0.0.0.0"), fall back to settings.NSOT_PORT
  instead of None to prevent a crash in the HTTP service layer.

Closes #23

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>


## v2.0.3 (2026-02-09)

### Bug Fixes

- Include regex pattern in attribute name validation error
  ([`b782ca9`](https://github.com/jathanism/nsot/commit/b782ca9fb5d619b26fa88286ab821295227e66f0))

Show the required pattern in the error message so users know what format is expected for attribute
  names.

Closes #21

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

### Continuous Integration

- Skip redundant CI run on merge to main
  ([`e02e738`](https://github.com/jathanism/nsot/commit/e02e738bd52f4817ac128239f27eff68f943f3cc))

Tests, lint, and build already run on the PR branch. Running them again on the push to main is
  redundant.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>


## v2.0.2 (2026-02-09)

### Bug Fixes

- Default timezone to UTC and enable timezone-aware datetimes
  ([`135239f`](https://github.com/jathanism/nsot/commit/135239f4f3c58c948a1a0f0c2f8607cdd1ef3036))

Set TIME_ZONE = "UTC" and USE_TZ = True so that Django stores and displays datetimes in UTC. A
  network infrastructure tool should not default to America/Chicago.

Closes #20

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

### Documentation

- Clarify superuser creation in quickstart guide
  ([`d57c057`](https://github.com/jathanism/nsot/commit/d57c0574d38d4426507d5d931641fdd49096947f))

Rewrite step 3 to explain that NSOT_NEW_USERS_AS_SUPERUSER=True is the default, so header-auth users
  are auto-created as superusers. Move createsuperuser to a tip for session/basic auth users. Add uv
  as an alternative install method.

Closes #25

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

- Document NSOT_NEW_USERS_AS_SUPERUSER setting
  ([`11427f6`](https://github.com/jathanism/nsot/commit/11427f60ee8d0a44c06a091be0f245905d8897e2))

Add an Authentication section to docs/config.rst explaining the NSOT_NEW_USERS_AS_SUPERUSER setting,
  its default value, scope, and security implications. Also add it (commented out) to the config
  template emitted by nsot-server init.

Closes #24

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>


## v2.0.1 (2026-02-09)

### Bug Fixes

- Modernize Docker setup for Python 3.12 and uv
  ([`2c2ab56`](https://github.com/jathanism/nsot/commit/2c2ab5623dccb760a06f430c04c643f9e31717f3))

Rewrite the Docker setup to work with the modernized codebase:

- Multi-stage Dockerfile: uv builder + python:3.12-slim-bookworm runtime - Simplified SQLite-only
  config with /var/lib/nsot data directory - docker-compose.yml with named volume for persistence -
  Non-root container user - .dockerignore for clean builds - Updated docs with docker compose
  quickstart

Closes #13

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

### Documentation

- Add .readthedocs.yaml and update README & Sphinx docs for v2.0.0
  ([`60bc328`](https://github.com/jathanism/nsot/commit/60bc32840650b7675007a3ae6a62dbebc134ac0e))

- Add .readthedocs.yaml for RTD v2 builds with Python 3.11 and pip install .[docs] - Rewrite
  README.md: fix logo URL, update badges, add What's New section, modern install/dev instructions,
  updated resources - Update docs/conf.py copyright to 2014-2026, Jathan McCollum - Replace Travis
  CI badge with GitHub Actions in docs/index.rst - Fix GitHub URLs from dropbox/nsot to
  jathanism/nsot across all docs - Update Python requirement from 2.7 to 3.10+ in
  docs/installation.rst - Modernize docs/development.rst: uv workflow, ruff, semantic-release -
  Update Django docs links from 1.8 to 5.2 in docs/config.rst - Remove dead Freenode IRC link, add
  GitHub Issues in docs/support.rst - Modernize docs/install/ubuntu.rst for Ubuntu 22.04 with
  python3 packages - Add deprecation notes to centos, fedora, suse, macosx install guides

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>


## v2.0.0 (2026-02-08)

### Chores

- Transition changelog for semantic-release
  ([`26b799f`](https://github.com/jathanism/nsot/commit/26b799f427c42a604b31313bb4b3fc5c904d44b7))

- Rename CHANGELOG.rst to CHANGELOG-legacy.rst - Create CHANGELOG.md managed by semantic-release

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

### Continuous Integration

- Add GitHub Actions workflows and pre-commit config
  ([`2f4788b`](https://github.com/jathanism/nsot/commit/2f4788bddf97043a96be40f74c351963ab51d5c6))

- ci.yml: test matrix (3.10, 3.11, 3.12) + ruff lint + build - release.yml: semantic-release + PyPI
  trusted publishing - release-preview.yml: PR comment with next version preview -
  .pre-commit-config.yaml: ruff + standard hooks

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

- Generate uv.lock
  ([`1afd8f5`](https://github.com/jathanism/nsot/commit/1afd8f55a72418b6e2bf73af90abb78f0996c4b8))

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

- Replace poetry with uv+setuptools and add ruff config
  ([`aec39e5`](https://github.com/jathanism/nsot/commit/aec39e581d0c784d5755c9dc3b026c09a1f5e14d))

- Rewrite pyproject.toml from Poetry to PEP 621 + setuptools - Add ruff lint/format config (replaces
  flake8+black) - Add semantic-release config for automated releases - Add pytest config (migrated
  from setup.cfg) - Add .python-version (3.11) - Update .gitignore for ruff, venv, worktrees -
  Convert README.rst to README.md - Delete poetry.lock, setup.cfg, bump.sh

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

### Documentation

- Update CLAUDE.md for uv and ruff tooling
  ([`37ddcff`](https://github.com/jathanism/nsot/commit/37ddcffc6b64f9a7614dbc7d4b9fd66958c5bf61))

Replace poetry/flake8/black commands with uv/ruff equivalents.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

### Refactoring

- Simplify version.py for Python 3.10+
  ([`6a15587`](https://github.com/jathanism/nsot/commit/6a155876ad9420b12e4279a337a66edf03c3e206))

Remove importlib_metadata fallback that was needed for Python <3.8.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
