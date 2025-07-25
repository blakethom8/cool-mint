import sys
import os
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config
from sqlalchemy import pool

# Add the project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

from database.database_utils import DatabaseUtils
from database.session import Base

# This import is required for autogenerate support
from database.event import *
from database.data_models.salesforce_data import *  # Import Salesforce models
from database.data_models.proc_dx_tables import *  # Import procedure/diagnosis models
from database.data_models.claims_data import *  # Import claims data models
from database.data_models.activity_bundles import *  # Import activity bundle models
from database.data_models.crm_lookups import *  # Import CRM lookup tables first
from database.data_models.relationship_management import *  # Import CRM relationship models
from database.data_models.crm_general import *  # Import CRM general models
from database.data_models.email_data import *  # Import email data models
from database.data_models.email_parsed_data import *  # Import email parsed data models

"""
Alembic Environment Module

This module provides the environment for Alembic migrations.
"""

load_dotenv()


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata

# Base.metadata.create_all(engine)

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

config.set_main_option("sqlalchemy.url", DatabaseUtils.get_connection_string())


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
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
