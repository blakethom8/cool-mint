import os
import pathlib
import sys

from database.database_utils import DatabaseUtils

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

import pytest
from alembic.config import Config
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from alembic import command
from database.session import Base

load_dotenv()


@pytest.fixture(scope="session")
def engine():
    os.environ["DATABASE_HOST"] = os.environ["TEST_DATABASE_HOST"]
    os.environ["DATABASE_PORT"] = os.environ["TEST_DATABASE_PORT"]
    os.environ["DATABASE_NAME"] = os.environ["TEST_DATABASE_NAME"]
    os.environ["DATABASE_USER"] = os.environ["TEST_DATABASE_USER"]
    os.environ["DATABASE_PASSWORD"] = os.environ["TEST_DATABASE_PASSWORD"]

    connection_string = DatabaseUtils.get_connection_string()
    engine = create_engine(connection_string, echo=True)
    Base.metadata.bind = engine
    return engine


@pytest.fixture(scope="session")
def connection(engine):
    connection = engine.connect()
    yield connection
    connection.close()


@pytest.fixture(scope="session")
def setup_database(connection):
    os.environ["DATABASE_HOST"] = os.environ["TEST_DATABASE_HOST"]
    os.environ["DATABASE_PORT"] = os.environ["TEST_DATABASE_PORT"]
    os.environ["DATABASE_NAME"] = os.environ["TEST_DATABASE_NAME"]
    os.environ["DATABASE_USER"] = os.environ["TEST_DATABASE_USER"]
    os.environ["DATABASE_PASSWORD"] = os.environ["TEST_DATABASE_PASSWORD"]

    alembic_cfg = Config(
        str(pathlib.Path(__file__).resolve().parents[1] / "alembic.ini")
    )
    alembic_cfg.set_main_option(
        "script_location",
        str(pathlib.Path(__file__).resolve().parents[1] / "alembic"),
    )
    alembic_cfg.attributes["connection"] = connection

    with connection.begin() as transaction:
        command.upgrade(alembic_cfg, "head")
    yield
    transaction.rollback()


@pytest.fixture(scope="function")
def session(setup_database, connection):
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
