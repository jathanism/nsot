# NSoT Docker Image

Run NSoT in a container. The image builds from source using
[uv](https://docs.astral.sh/uv/) and runs on Python 3.12 with SQLite.

## Quick Start (docker compose)

```bash
docker compose up -d
```

This builds the image, runs migrations, collects static files, and starts
NSoT on port **8990**.

Create a superuser to log in:

```bash
docker compose exec nsot nsot-server createsuperuser --email admin@example.com
```

Then visit <http://localhost:8990/>.

## Manual Build

```bash
docker build -f docker/Dockerfile -t nsot .
docker run -p 8990:8990 -e NSOT_SECRET=$(python3 -c "import base64,os;print(base64.urlsafe_b64encode(os.urandom(32)).decode())") nsot
```

## Environment Variables

| Variable      | Default                          | Description                              |
|:--------------|:---------------------------------|:-----------------------------------------|
| `NSOT_SECRET` | *(built-in dev key)*             | 32-byte URL-safe base64 secret key       |
| `NSOT_EMAIL`  | `X-NSoT-Email`                   | Header for reverse-proxy authentication  |
| `DB_NAME`     | `/var/lib/nsot/nsot.sqlite3`     | Path to SQLite database file             |

### Generating a secret key

```bash
python3 -c "import base64, os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
```

## Data Persistence

The `docker-compose.yml` uses a named volume (`nsot-data`) mounted at
`/var/lib/nsot` so the SQLite database survives container restarts.

For manual `docker run`, mount a volume:

```bash
docker run -p 8990:8990 -v nsot-data:/var/lib/nsot nsot
```

## Management Commands

Run any `nsot-server` management command via `docker compose exec`:

```bash
docker compose exec nsot nsot-server dbshell
docker compose exec nsot nsot-server shell_plus
docker compose exec nsot nsot-server createsuperuser --email you@example.com
```

## Ports

Only TCP **8990** is exposed.

## Custom Configuration

To provide a fully custom config file, volume-mount it over
`/etc/nsot/nsot.conf.py`:

```bash
docker run -p 8990:8990 -v ./my-nsot.conf.py:/etc/nsot/nsot.conf.py nsot
```
