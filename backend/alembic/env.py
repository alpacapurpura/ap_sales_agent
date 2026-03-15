from logging.config import fileConfig
import os
import sys

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# --- CUSTOM CONFIGURATION ---
# Add project root to python path to import app modules
sys.path.append(os.getcwd())

# Import Settings (to get DB URL) and Base (to get Metadata)
from src.core.config import settings
from src.shared.domain.base_entity import Base
# Must import all models to ensure they are registered in metadata
from src.modules.assets.infrastructure import models as assets_models
from src.modules.iam.infrastructure.models import UserModel, TenantModel, UserTenantModel
from src.modules.crm.infrastructure.models import lead_model
from src.modules.connections.domain import channel as channel_connection
from src.modules.scheduling.infrastructure.models import appointment_model as appointment, booking_link
from src.modules.sales_agent.infrastructure.models import message_model as message
from src.shared.links.models import ShareableLink
from src.modules.crm.infrastructure.models import customer_model

from src.modules.brand.infrastructure.models import avatar_model
from src.modules.offer.infrastructure import models as offer_models
from src.modules.landing.infrastructure.models import landing_model
from src.modules.analytics.infrastructure.models import (  # noqa: F401 — ETL tables
    StagingMetricModel,
    OfficialMetricModel,
    ExtractionRunModel,
    MetricAggregationModel,
)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Overwrite sqlalchemy.url with the one from settings
db_url = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
config.set_main_option("sqlalchemy.url", db_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
