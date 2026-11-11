from alembic import context
from sqlalchemy import create_engine, pool

from app.core.config import DATABASE_URL
from app.core.database import Base
from app import models  # Registra Equipamento na metadata.


config = context.config
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = DATABASE_URL.render_as_string(hide_password=False)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(DATABASE_URL, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()
    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
