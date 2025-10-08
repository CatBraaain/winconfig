from textwrap import dedent
from typing import Literal

from pydantic import BaseModel, ConfigDict, RootModel

# Why use PowerShell instead of reg.exe, sc.exe, or schtasks.exe?
# ---------------------------------------------------------------
# Tools like reg.exe, sc.exe, and schtasks.exe are effective for setting values
# but not for retrieving them in a structured format.
# PowerShell, on the other hand, allows reading and modifying system configuration
# objects (e.g., registry entries, services, scheduled tasks) as native objects.
# This makes it easier to verify that the expected values were applied correctly
# during automated testing.

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
    old_value: str | Literal["<RemoveEntry>"]  # noqa: PYI051
    new_value: str | Literal["<RemoveEntry>"]  # noqa: PYI051


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


class DefinitionContainer(RootModel):
    root: list[Definition] = []

    def get_definition(self, task_name: str) -> Definition:
        definition = next((x for x in self.root if x.name == task_name), None)
        if definition is None:
            raise ValueError(f"Definition {task_name} not found")
        return definition
