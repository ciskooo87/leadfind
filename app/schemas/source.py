from pydantic import BaseModel


class SourceRead(BaseModel):
    id: int
    name: str
    source_type: str
    reliability_score: float
    active: str

    model_config = {"from_attributes": True}
