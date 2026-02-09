# NSoT

![Network Source of Truth](https://raw.githubusercontent.com/jathanism/nsot/main/docs/_static/logo_128.png)

[![CI](https://github.com/jathanism/nsot/actions/workflows/ci.yml/badge.svg)](https://github.com/jathanism/nsot/actions/workflows/ci.yml)
[![Documentation Status](https://readthedocs.org/projects/nsot/badge/?version=latest&style=flat)](https://nsot.readthedocs.io/)
[![PyPI Status](https://img.shields.io/pypi/v/nsot.svg?style=flat)](https://pypi.org/project/nsot/)

Network Source of Truth (NSoT) is a source of truth database and repository for
tracking inventory and metadata of network entities to ease management and
automation of network infrastructure.

NSoT is an API-first application that provides a REST API for managing IP
addresses (IPAM), network devices, and network interfaces.

NSoT was originally created at [Dropbox](https://github.com/dropbox/nsot) and
is now maintained by [Jathan McCollum](https://github.com/jathanism).

## What's New in v2.0.0

- Upgraded to **Django 5.2** and **Django REST Framework 3.16**
- Requires **Python 3.10+** (dropped Python 2.7 / 3.x < 3.10)
- Modern tooling: **uv** for dependency management, **ruff** for linting/formatting
- CI/CD via **GitHub Actions** with **python-semantic-release**

## Installation

```bash
pip install nsot
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add nsot
```

## Quick Start

```bash
# Initialize the config (~/.nsot/nsot.conf.py)
nsot-server init

# Create a superuser
nsot-server createsuperuser --email admin@localhost

# Start the server on 8990/tcp
nsot-server start
```

Then browse the API at http://localhost:8990/api/ or the admin at http://localhost:8990/admin/.

## Development

```bash
git clone https://github.com/jathanism/nsot.git
cd nsot
uv sync --all-extras

# Run tests
NSOT_API_VERSION=1.0 uv run pytest -vv tests/

# Lint / format
uv run ruff check nsot/ tests/
uv run ruff format nsot/ tests/
```

## Resources

- [Documentation](https://nsot.readthedocs.io/)
- [Python API client / CLI utility (pyNSoT)](https://pynsot.readthedocs.io/)
- [GitHub Issues](https://github.com/jathanism/nsot/issues)
