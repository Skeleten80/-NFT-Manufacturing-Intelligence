import json
import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from time import monotonic
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from redis import Redis
from sqlalchemy import Engine, text
from starlette.exceptions import HTTPException
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from nft_api.config import Settings
from nft_api.db import make_engine
from nft_api.observability import ErrorReporter, NullErrorReporter, RequestMetrics

log = logging.getLogger("nft.requests")


class Dependencies:
    def __init__(self, engine: Engine, cache: Redis) -> None:
        self.engine = engine
        self.cache = cache

    def ready(self) -> bool:
        try:
            with self.engine.connect() as conn:
                role = conn.execute(
                    text(
                        "SELECT rolsuper, rolbypassrls, rolcreatedb, rolcreaterole FROM "
                        "pg_roles WHERE rolname = current_user"
                    )
                ).one()
                if any(role):
                    return False
                if (
                    conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                    != "0001"
                ):
                    return False
                if (
                    conn.execute(
                        text(
                            "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON "
                            "n.oid=c.relnamespace WHERE n.nspname='public' AND c.relname IN "
                            "('organizations','organization_members','audit_logs') AND "
                            "c.relrowsecurity AND c.relforcerowsecurity AND c.relowner <> "
                            "(SELECT oid FROM pg_roles WHERE rolname=current_user)"
                        )
                    ).scalar_one()
                    != 3
                ):
                    return False
            return bool(self.cache.ping())
        except Exception:
            return False

    def close(self) -> None:
        self.engine.dispose()
        self.cache.close()


def create_app(
    settings: Settings | None = None,
    readiness: Callable[[], bool] | None = None,
    error_reporter: ErrorReporter | None = None,
) -> FastAPI:
    log.setLevel(logging.INFO)
    if not log.handlers:
        log.addHandler(logging.StreamHandler())
    config = settings or Settings()
    dependencies = Dependencies(
        make_engine(config),
        Redis.from_url(
            config.redis_url.get_secret_value(), socket_timeout=2, socket_connect_timeout=2
        ),
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        yield
        dependencies.close()

    app = FastAPI(
        title="NFT Manufacturing Intelligence",
        version="0.0.1",
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url="/api/v1/openapi.json" if config.environment == "development" else None,
    )

    metrics = RequestMetrics()
    app.state.metrics = metrics
    reporter = error_reporter or NullErrorReporter()

    @app.middleware("http")
    async def request_context(request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = str(uuid4())
        request.state.request_id = request_id
        started = monotonic()
        try:
            response = await call_next(request)
        except Exception as exc:
            reporter.report(request_id, type(exc).__name__)
            response = JSONResponse(
                {
                    "error": {
                        "code": "internal_error",
                        "message": "Request failed",
                        "request_id": request_id,
                    }
                },
                status_code=500,
            )
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        if config.environment == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        metrics.observe(response.status_code, (monotonic() - started) * 1000)
        log.info(
            json.dumps(
                {
                    "request_id": request_id,
                    "method": request.method,
                    "status": response.status_code,
                    "duration_ms": round((monotonic() - started) * 1000, 2),
                }
            )
        )
        return response

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            {
                "error": {
                    "code": "http_error",
                    "message": "Request unavailable",
                    "request_id": request.state.request_id,
                }
            },
            status_code=exc.status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            {
                "error": {
                    "code": "validation_error",
                    "message": "Invalid input",
                    "request_id": request.state.request_id,
                }
            },
            status_code=422,
        )

    @app.get("/api/v1/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok", "product": "NFT Manufacturing Intelligence", "phase": "0"}

    @app.get("/api/v1/ready", tags=["system"])
    def ready() -> JSONResponse:
        good = (readiness or dependencies.ready)()
        return JSONResponse(
            {"status": "ready" if good else "unavailable"}, status_code=200 if good else 503
        )

    return app
