# CHANGELOG

This changelog is managed by [python-semantic-release](https://python-semantic-release.readthedocs.io/).

For the pre-2.0 changelog, see [CHANGELOG-legacy.rst](CHANGELOG-legacy.rst).

## v2.0.0 (2026-02-08)

### Breaking Changes

- **Python 3.10+ required** — dropped Python 2.7 and Python 3.x < 3.10
- **Django 5.2** — upgraded from Django 1.x through 3.1, 4.2, to 5.2 LTS
- **Django REST Framework 3.16** — upgraded from DRF 3.3

### Highlights

- Modernized all Django APIs: replaced `django.conf.urls.url()` with `django.urls.re_path()`, updated middleware to modern style, replaced `django.utils.encoding` and `django.utils.translation` imports
- Vendored `djangorestframework-bulk` into `nsot/vendor/` for Django 5.2 compatibility
- Replaced `setup.py` + `requirements*.txt` with `pyproject.toml` + `uv` for dependency management
- Replaced `flake8` + `isort` with `ruff` for linting and formatting
- Replaced Travis CI with GitHub Actions (CI + release workflows)
- Automated releases via python-semantic-release with PyPI trusted publishing
