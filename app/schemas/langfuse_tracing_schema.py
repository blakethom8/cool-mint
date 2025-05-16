from datetime import datetime

from pydantic import BaseModel


class LangfuseTracingEventSchema(BaseModel):
    event: str
    timestamp: datetime
    comment_id: str
    thread_id: str
    user_id: str
    content: str
