from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import RootModel


class TaskMode(Enum):
    APPLY = "apply"
    REVERT = "revert"
    SKIP = "skip"

    def resolve(self, reverse: bool) -> TaskMode:
        if reverse:
            if self == TaskMode.APPLY:
                return TaskMode.REVERT
            if self == TaskMode.REVERT:
                return TaskMode.APPLY
        return self


type ApplyMode = Literal[TaskMode.APPLY, TaskMode.REVERT]


class TaskPlan(RootModel):
    root: dict[str, dict[str, TaskMode]] = {}
