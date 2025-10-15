import re
import subprocess
from pathlib import Path
from typing import Annotated, Any, Literal

import yaml
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


class RegistryDefinition(BaseModel):
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


type SchtaskState = Literal["Enabled", "Disabled"]


class SchtaskDefinition(BaseModel):
    full_path: str
    old_state: SchtaskState
    new_state: SchtaskState

    def resolve_value(self, revert: bool) -> str:
        return self.new_state if not revert else self.old_state

    @property
    def formatted_path(self) -> str:
        return "\\" + self.full_path.removeprefix("\\")

    @property
    def path(self) -> str:
        return str(Path(self.formatted_path).parent.as_posix()) + "/"

    @property
    def name(self) -> str:
        return Path(self.formatted_path).name


type ServiceStartupType = Literal[
    "Automatic",
    "AutomaticDelayedStart",
    "Disabled",
    "InvalidValue",
    "Manual",
]


class ServiceDefinition(BaseModel):
    name: str
    old_startup: ServiceStartupType
    new_startup: ServiceStartupType

    def resolve_value(self, revert: bool) -> str:
        return self.new_startup if not revert else self.old_startup


class ScriptDefinition(BaseModel):
    apply: str | None
    revert: str | None

    def resolve_value(self, revert: bool) -> str | None:
        return self.apply if not revert else self.revert


class TaskDefinition(BaseModel):
    id: str
    name: str
    description: str
    registries: list[RegistryDefinition] = []
    scheduled_tasks: list[SchtaskDefinition] = []
    services: list[ServiceDefinition] = []
    script: ScriptDefinition = ScriptDefinition(apply=None, revert=None)

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


class Definition(BaseModel):
    task_definitions: list[TaskDefinition] = []
    preload: str | None = None

    def get_task_definition(self, task_name: str) -> TaskDefinition:
        task = next((x for x in self.task_definitions if x.name == task_name), None)
        if task is None:
            raise ValueError(f"Task definition {task_name} not found")
        return task

    def output_yaml(self, dist_path: str) -> None:
        def str_presenter(dumper: Any, data: Any) -> Any:  # noqa: ANN401
            if len(data.splitlines()) > 1:
                return dumper.represent_scalar(
                    "tag:yaml.org,2002:str",
                    data.removeprefix("\ufeff").replace("\t", "    "),
                    style="|",
                )
            return dumper.represent_scalar("tag:yaml.org,2002:str", data)

        yaml.add_representer(str, str_presenter)

        schema_ref_str = "# yaml-language-server: $schema=./schema.json"
        yaml_str = (
            schema_ref_str
            + "\n\n"
            + yaml.dump(
                self.model_dump(exclude_defaults=True),
                allow_unicode=True,
                sort_keys=False,
            )
        )

        Path(dist_path).write_text(yaml_str, encoding="utf-8")
        subprocess.run(["bunx", "prettier", "--write", f'"{dist_path}"'], check=True)
