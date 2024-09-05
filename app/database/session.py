from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from database.database_utils import DatabaseUtils

engine = create_engine(DatabaseUtils.get_connection_string())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
