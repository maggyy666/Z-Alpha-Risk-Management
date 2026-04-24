# Z-Alpha Securities - Risk Management System

Portfolio risk analytics platform. Four services on Docker Desktop
Kubernetes: `frontend` (Next.js), `user-api` (auth + JWT), `backend`
(portfolio + analytics + IBKR), `postgres`.

## Prerequisites

- **Docker Desktop** with **Kubernetes enabled**
  (Settings -> Kubernetes -> Enable Kubernetes; wait for the green light)
- **Python 3.11** -- required by the Interactive Brokers API
- **Poetry** -- [install](https://python-poetry.org/docs/)
- **TWS (Trader Workstation)** running on the host with API enabled
  (live: 7496, paper: 7497). Live accounts with 2FA stay on the host; we
  do not containerize TWS.

## Quick start

```bash
# 1. Set passwords + AUTH_SECRET
cp config.env.example .env
# edit .env: ADMIN_PASSWORD, USER_PASSWORD, POSTGRES_PASSWORD, AUTH_SECRET

# 2. Install Python deps (one-time)
poetry install

# 3. Point kubectl at Docker Desktop's cluster (one-time)
kubectl config use-context docker-desktop

# 4. Go
python start_all.py
```

`start_all.py` loads `.env`, checks tools and TWS reachability, builds both
images with a per-run tag, applies the manifests in `deploy/`, seeds the
database inside the backend pod, and waits for every rollout.

## Endpoints

- Frontend:    http://localhost:3000
- Backend API: http://localhost:8000 (docs at `/docs`)
- User API:    http://localhost:8001

All three are `type: LoadBalancer` -- Docker Desktop auto-maps LoadBalancer
services to `localhost` on the service `port`.

## Default users

`setup_database.py` seeds two users from `.env` on every run (drops and
recreates the schema, so this is idempotent):

- `admin` / `$ADMIN_PASSWORD`
- `user`  / `$USER_PASSWORD`

## Verify the JWT flow

```bash
TOKEN=$(curl -s -X POST http://localhost:8001/auth/login \
  -H 'Content-Type: application/json' \
  -d "{\"username\":\"admin\",\"password\":\"$ADMIN_PASSWORD\"}" | jq -r .access_token)

curl -s http://localhost:8001/auth/me     -H "Authorization: Bearer $TOKEN"
curl -s http://localhost:8000/auth/verify -H "Authorization: Bearer $TOKEN"
```

`user-api` issues HS256 tokens signed with `AUTH_SECRET`; `backend` verifies
with the same secret. The shared secret lives in the `zalpha-secrets`
Kubernetes Secret, generated from `.env` at apply time.

## After code changes

```bash
python start_all.py
```

Idempotent. Rebuilds images, bumps `kubectl set image` with a fresh tag,
re-seeds the DB.

## Teardown

```bash
kubectl delete namespace zalpha
```

## Environment variables (`.env`)

| Variable | Purpose |
| --- | --- |
| `POSTGRES_PASSWORD` | DB password |
| `ADMIN_PASSWORD`, `USER_PASSWORD` | Seeded user passwords (>= 8 chars) |
| `AUTH_SECRET` | JWT signing key -- `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `IBKR_HOST`, `IBKR_PORT` | Default `host.docker.internal:7496` (live) / `7497` (paper) |

`.env` is gitignored -- never commit it.

## Troubleshooting

- **`Missing CLI tools on PATH: kubectl`** -- install `kubectl`, or restart
  the shell so PATH refreshes.
- **`kubectl context is '...', expected 'docker-desktop'`** -- enable
  Kubernetes in Docker Desktop, then
  `kubectl config use-context docker-desktop`.
- **`IBKR TWS not reachable`** -- start TWS, enable API, whitelist
  `127.0.0.1` in TWS settings.
- **Ports 3000/8000/8001 busy** -- `docker ps` / `netstat -ano`; stop
  whatever holds them.
- **Pods stuck on old code after a rebuild** -- shouldn't happen (per-run
  image tag triggers `kubectl set image`), but as a manual escape:
  `kubectl -n zalpha rollout restart deploy/backend deploy/user-api deploy/frontend`.

## Alternative: docker-compose

`docker-compose.yml` is retained as a secondary dev path. It does not use
the K8s manifests and won't exercise the `user-api` / JWT split. Prefer
Kubernetes for anything beyond a quick sanity check.
