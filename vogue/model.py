from enum import Enum
from pydantic import BaseModel, Field as PField, computed_field


class Field(str, Enum):
    HUMANITIES = "humanities"
    SOCIAL = "social"
    LIFE = "life"
    PHYS = "phys"
    ENG = "eng"
    OTHER = "other"
    UNKNOWN = "unknown"


class Record(BaseModel):
    source: str
    id: str
    title: str
    year: int | None
    discipline_raw: str
    field: Field
    work_type: str
    url: str
    abstract: str | None = None
    raw: dict = PField(default_factory=dict)

    @computed_field
    @property
    def key(self) -> str:
        return f"{self.source}:{self.id}"
