# syntax=docker/dockerfile:1

# ---- Build stage ----
FROM ghcr.io/astral-sh/uv:0.6-python3.12-bookworm-slim AS builder

WORKDIR /build

# Copy dependency metadata first for better layer caching
COPY pyproject.toml uv.lock README.md ./
COPY nsot/ nsot/

# Install dependencies into a virtual environment (no dev deps, no editable)
RUN uv sync --frozen --no-dev --no-editable

# ---- Runtime stage ----
FROM python:3.12-slim-bookworm

# Install sqlite3 CLI for dbshell support
RUN apt-get update -qq \
    && apt-get install -y --no-install-recommends sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --system nsot && useradd --system --gid nsot nsot

# Copy virtual environment from builder
COPY --from=builder /build/.venv /opt/nsot-venv

# Put the venv on PATH so nsot-server is available
ENV PATH="/opt/nsot-venv/bin:$PATH"

# Point logan runner at the Docker config file
ENV NSOT_CONF=/etc/nsot/nsot.conf.py

# Copy Docker-specific config
COPY docker/conf /etc/nsot

# Create data directory for SQLite persistence
RUN mkdir -p /var/lib/nsot && chown nsot:nsot /var/lib/nsot

EXPOSE 8990

USER nsot

ENTRYPOINT ["nsot-server"]
CMD ["start", "--noinput"]
