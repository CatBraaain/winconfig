from pydantic import BaseModel, ConfigDict, RootModel


class Task(BaseModel):
    task_name: str
    revert: bool = False

    model_config = ConfigDict(
        extra="forbid",
    )


class Config(RootModel):
    root: list[Task] = []
