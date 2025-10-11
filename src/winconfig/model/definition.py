import re
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    PlainSerializer,
    field_validator,
)

from winconfig.powershell.constants import NotExistType

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
    path: Annotated[str, PlainSerializer(lambda x: x.replace("Registry::", ""))]
    name: str
    type: RegistryValueKind
    old_value: str | NotExistType
    new_value: str | NotExistType

    @field_validator("path", mode="after")
    @staticmethod
    def normalize_path(value: str) -> str:
        mapping = {
            r"(HKEY_CLASSES_ROOT|HKCR):?\\": r"HKCR\\",
            r"(HKEY_CURRENT_CONFIG|HKCC):?\\": r"HKCC\\",
            r"(HKEY_CURRENT_USER|HKCU):?\\": r"HKCU\\",
            r"(HKEY_LOCAL_MACHINE|HKLM):?\\": r"HKLM\\",
            r"(HKEY_USERS|HKU):?\\": r"HKU\\",
        }

        for pattern, repl in mapping.items():
            value = re.sub(
                "^(Registry::)?" + pattern,
                "Registry::" + repl,
                value,
                flags=re.IGNORECASE,
            )
        return value

    @property
    def full_path(self) -> str:
        return f"{self.path.replace('Registry::', '')}\\{self.name}"

    def resolve_value(self, revert: bool) -> str:
        return self.new_value if not revert else self.old_value


type ScheduledTaskState = Literal["Enabled", "Disabled"]


class ScheduledTask(BaseModel):
    full_path: str
    old_state: ScheduledTaskState
    new_state: ScheduledTaskState

    def resolve_value(self, revert: bool) -> str:
        return self.new_state if not revert else self.old_state

    @property
    def path(self) -> str:
        return self.full_path.rsplit("\\", 1)[0]

    @property
    def name(self) -> str:
        return self.full_path.rsplit("\\", 1)[1]


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

    def resolve_value(self, revert: bool) -> str:
        return self.new_startup_type if not revert else self.old_startup_type


class Script(BaseModel):
    apply: str | None
    revert: str | None

    def resolve_value(self, revert: bool) -> str | None:
        return self.apply if not revert else self.revert


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


class DefinitionContainer(BaseModel):
    definitions: list[Definition] = []
    preload: str | None = None

    def get_definition(self, task_name: str) -> Definition:
        definition = next((x for x in self.definitions if x.name == task_name), None)
        if definition is None:
            raise ValueError(f"Definition {task_name} not found")
        return definition
