import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID

from database.session import Base


class Event(Base):
    __tablename__ = "events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid1)

    data = Column(JSON)
    task_context = Column(JSON)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
