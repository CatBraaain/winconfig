from enum import Enum
from typing import Literal

from pydantic import RootModel


class TaskMode(Enum):
    APPLY = "apply"
    REVERT = "revert"
    SKIP = "skip"


type ApplyMode = Literal[TaskMode.APPLY, TaskMode.REVERT]


class TaskPlan(RootModel):
    root: dict[str, TaskMode] = {}
