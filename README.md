# NFT Manufacturing Intelligence

**NFT — Next-Gen Factory Technologies** · Phase 0 foundation · 0.0.1

Start with [the Phase 0 report](docs/phase-0-completion-report.md). It records actual results and remaining gates; generated code is not proof of a completed phase. No Phase 1 identity workflows have been implemented.

## Included

Architecture/critique, normalized schema proposal, four-table Alembic foundation, PostgreSQL isolation policies, permission primitives, structured API logging, health/readiness, a clearly labeled Next.js foundation screen, Docker Compose, locked dependencies, CI and adversarial security tests. No manufacturing records or model output are fabricated.

## Local development with Docker

Requirements: Docker Engine with Compose v2; Python 3.12+ for the local environment generator.

```sh
python3 scripts/init_env.py
docker compose up --build -d --wait
```

Open http://localhost:3000. API liveness: http://localhost:8000/api/v1/health. Readiness: http://localhost:8000/api/v1/ready. OpenAPI JSON: http://localhost:8000/api/v1/openapi.json. This is a foundation screen, not an operational Command Center. Interactive API docs are deferred; consume the OpenAPI JSON in a local client.

```sh
docker compose logs --tail=100 api
docker compose down
```

Ordinary shutdown preserves data. Never delete the production volume to fix a migration. Initial DB role creation happens only on an empty volume; changing .env after initialization does not rotate database credentials. See operations.md for rotation and recovery.

## Native development

Requirements: Node 24, Python 3.12, uv; a provisioned PostgreSQL 17 database and Redis 7. Use different migration and runtime credentials. Reproduce `infra/docker/init-db.sh` using a DBA connection first. Do not use the migration role in the API.

```sh
uv sync --frozen
npm ci
# Set NFT_MIGRATION_DATABASE_URL to the migration connection securely.
uv run alembic upgrade head
# Set NFT_DATABASE_URL to the restricted runtime connection and NFT_REDIS_URL.
uv run uvicorn nft_api.main:create_app --factory --port 8000 --no-access-log
# In a second terminal:
npm run dev
```

Docker hostnames in generated .env are for Compose; native execution requires localhost or your actual private service host. Never paste credentials into logs or source control. `/ready` returns 503 when dependencies, schema revision, forced policies or runtime-role checks fail.

## Verification

Use a **disposable, migrated PostgreSQL database**, not a shop database. Set NFT_MIGRATION_DATABASE_URL, NFT_TEST_ADMIN_URL and NFT_TEST_RUNTIME_URL to it. The test admin must be able to seed both tenants; CI uses a disposable superuser. Runtime must have the restrictions from init-db.sh.

```sh
npx playwright install chromium
sh scripts/verify.sh
```

The verification script is fail-fast and includes database tests. For explicitly limited local feedback:

```sh
uv run pytest -q -m 'not database'
uv run ruff check apps/api tests scripts
uv run ruff format --check apps/api tests scripts
uv run mypy
npm run lint
npm run format:check
npm run typecheck
npm test
npm run build
npm run test:e2e
```

That subset does **not** clear the Phase 0 gate. DB tests fail if PostgreSQL variables are missing. Generated migration SQL is only a review artifact, not evidence that migrations ran. GitHub Actions provisions PostgreSQL and executes the complete script plus Docker builds and a downgrade/upgrade round-trip on its disposable DB.

## Documentation

- [Architecture, critique and roadmap](docs/architecture.md)
- [Schema proposal](docs/schema.md)
- [Metrics contracts](docs/metrics.md)
- [Security model](docs/security.md)
- [Operations and recovery](docs/operations.md)
- [Phase 0 completion report](docs/phase-0-completion-report.md)

No account registration, sessions, machines, jobs, production, analytics calculations, AI providers, edge connectivity or billing flows exist yet. Phase 1 requires explicit authorization after all Phase 0 gates pass.
