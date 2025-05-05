from pydantic import BaseModel


class PlaceholderEventSchema(BaseModel):
    id: str
    type: str
