from pydantic import BaseModel, ConfigDict, RootModel


class WinConfig(BaseModel):
    task_name: str
    revert: bool = False

    model_config = ConfigDict(
        extra="forbid",
    )


class ConfigTaskList(RootModel):
    root: list[WinConfig] = []
