import logging
from typing import Generator

from sqlalchemy.orm import Session

from database.session import SessionLocal


def db_session() -> Generator:
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as ex:
        session.rollback()
        logging.error(ex)
        raise ex
    finally:
        session.close()
