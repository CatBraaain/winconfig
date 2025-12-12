from pydantic import BaseModel, ConfigDict, Field

from .definition import Definition
from .task_plan import TaskPlan


class Config(BaseModel):
    definition: Definition = Field(
        default=Definition(),
        alias="Definition",
    )
    plan: TaskPlan = Field(
        default=TaskPlan(),
        alias="Plan",
    )

    model_config = ConfigDict(
        extra="forbid",
        validate_by_name=True,
        validate_by_alias=True,
    )
