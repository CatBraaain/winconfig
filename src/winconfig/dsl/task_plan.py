from pydantic import RootModel

from .const_types import TaskMode


class TaskPlan(RootModel):
    root: dict[str, TaskMode] = {}
