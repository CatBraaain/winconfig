from enum import StrEnum, auto
from typing import Literal

from pydantic import BaseModel, ConfigDict, RootModel

type RegistryValueKind = Literal[
    "String",
    "ExpandString",
    "Binary",
    "DWord",
    "MultiString",
    "QWord",
]


class Registry(BaseModel):
    path: str
    name: str
    type: RegistryValueKind
    old_value: str | None
    new_value: str | None


type ScheduledTaskState = Literal["Enabled", "Disabled"]


class ScheduledTask(BaseModel):
    path: str
    old_state: ScheduledTaskState
    new_state: ScheduledTaskState


type ServiceStartupType = Literal[
    "Automatic",
    "AutomaticDelayedStart",
    "Disabled",
    "InvalidValue",
    "Manual",
]


class Service(BaseModel):
    name: str
    old_startup_type: ServiceStartupType
    new_startup_type: ServiceStartupType


class Script(BaseModel):
    apply: str | None
    revert: str | None


class Definition(BaseModel):
    name: str
    description: str
    registries: list[Registry] = []
    scheduled_tasks: list[ScheduledTask] = []
    services: list[Service] = []
    script: Script = Script(apply=None, revert=None)

    model_config = ConfigDict(
        # use_enum_values=False,
        extra="forbid",
        json_schema_extra={
            "anyOf": [
                {"required": ["registries"]},
                {"required": ["scheduled_tasks"]},
                {"required": ["services"]},
                {"required": ["script"]},
            ]
        },
    )


class Definitions(RootModel):
    root: list[Definition] = []
