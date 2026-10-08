from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TodoStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    done = "done"


class _StrictModel(BaseModel):
    # Rechaza campos desconocidos y recorta espacios en los strings.
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class TodoCreate(_StrictModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: TodoStatus = TodoStatus.pending


class TodoUpdate(_StrictModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: TodoStatus | None = None

    @field_validator("title", "status")
    @classmethod
    def _not_null(cls, value):
        # Solo se ejecuta si el campo viene en el body: null explícito no vale.
        if value is None:
            raise ValueError("no puede ser null; omite el campo para no modificarlo")
        return value

    @model_validator(mode="after")
    def _at_least_one_field(self):
        if not self.model_fields_set:
            raise ValueError("indica al menos un campo: title, description o status")
        return self


class TodoOut(BaseModel):
    id: int
    title: str
    description: str | None
    status: TodoStatus
    created_at: str
    updated_at: str
