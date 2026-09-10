from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session

from nft_api.config import Settings
from nft_api.security import AuthorizedContext


def make_engine(settings: Settings) -> Engine:
    return create_engine(
        settings.database_url.get_secret_value(),
        pool_pre_ping=True,
        connect_args={"connect_timeout": 3},
        pool_size=5,
        max_overflow=5,
    )


@contextmanager
def tenant_session(engine: Engine, context: AuthorizedContext) -> Iterator[Session]:
    """Transaction-local setting prevents scope leaking on pooled connections."""
    with Session(engine) as session, session.begin():
        session.execute(
            text("SELECT set_config('nft.organization_id', :tenant, true)"),
            {"tenant": str(context.organization_id)},
        )
        yield session
