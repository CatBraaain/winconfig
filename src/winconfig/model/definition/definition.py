import re
import subprocess
from pathlib import Path
from typing import Annotated, Any, Literal

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PlainSerializer,
    field_validator,
)

from winconfig.powershell.constants import NotExistType

type RegistryValueKind = Literal[
    "String",
    "ExpandString",
    "Binary",
    "DWord",
    "MultiString",
    "QWord",
]


class RegistryDefinition(BaseModel):
    """Represents a single registry value to be modified."""

    path: Annotated[
        str,
        PlainSerializer(lambda x: x.replace("Registry::", "")),
        Field(description="The path to the registry key."),
    ]
    name: str = Field(description="The name of the registry value.")
    type: RegistryValueKind = Field(description="The type of the registry value.")
    old_value: str | NotExistType = Field(
        description="The default value of the registry entry."
    )
    new_value: str | NotExistType = Field(
        description="The desired value of the registry entry."
    )

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
    """Represents a scheduled task to be enabled or disabled."""

    full_path: str = Field(description="The full path of the scheduled task.")
    old_state: SchtaskState = Field(
        description="The default state of the scheduled task."
    )
    new_state: SchtaskState = Field(
        description="The desired state of the scheduled task."
    )

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
    """Represents a Windows service to be modified."""

    name: str = Field(description="The name of the service.")
    old_startup: ServiceStartupType = Field(
        description="The default startup type of the service."
    )
    new_startup: ServiceStartupType = Field(
        description="The desired startup type of the service."
    )

    def resolve_value(self, revert: bool) -> str:
        return self.new_startup if not revert else self.old_startup


class ScriptDefinition(BaseModel):
    """Represents PowerShell scripts to be executed."""

    apply: str | None = Field(
        description="The script to run for the desired configuration."
    )
    revert: str | None = Field(
        description="The script to run for the default configuration."
    )

    def resolve_value(self, revert: bool) -> str | None:
        return self.apply if not revert else self.revert


class TaskDefinition(BaseModel):
    """A single, self-contained configuration task."""

    id: str = Field(description="A unique identifier for the task.")
    name: str = Field(description="The name of the task.")
    description: str = Field(description="A description of the task's purpose.")
    registries: list[RegistryDefinition] = Field(
        default=[], description="The registry values to be modified."
    )
    scheduled_tasks: list[SchtaskDefinition] = Field(
        default=[], description="The scheduled tasks to be modified."
    )
    services: list[ServiceDefinition] = Field(
        default=[], description="The Windows services to be modified."
    )
    script: ScriptDefinition = Field(
        default=ScriptDefinition(apply=None, revert=None),
        description="Custom PowerShell scripts for actions not covered by registry, services, or scheduled tasks.",
    )

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
    """The root model for a winconfig definition file."""

    task_definitions: list[TaskDefinition] = Field(
        default=[], description="The list of configuration tasks to be applied."
    )
    preload: str | None = Field(
        None,
        description="Common PowerShell functions to be used by ScriptDefinition scripts.",
    )

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
