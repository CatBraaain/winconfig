import subprocess
from pathlib import Path
from typing import Any

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
)

from .const_types import (  # noqa: F401
    ApplyMode,
    NotExistType,
    TaskMode,
)
from .registry import (  # noqa: F401
    RegistryEntryDefinition,
    RegistryKeyDefinition,
    RegistryValueKind,
)
from .schtask import SchtaskDefinition, SchtaskState  # noqa: F401
from .script import ScriptDefinition
from .service import ServiceDefinition, ServiceStartupType  # noqa: F401


class TaskDefinition(BaseModel):
    """A single, self-contained configuration task."""

    name: str = Field(description="The name of the task.")
    description: str = Field(description="A description of the task's purpose.")
    registries: list[RegistryEntryDefinition | RegistryKeyDefinition] = Field(
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

    def generate_script(self, mode: TaskMode) -> str:
        script = "\n".join(
            [registry.generate_set_script(mode) for registry in self.registries]
            + [task.generate_set_script(mode) for task in self.scheduled_tasks]
            + [service.generate_set_script(mode) for service in self.services]
            + [self.script.generate_custom_script(mode)]
        )
        return script


class Definition(RootModel):
    """The root model for a winconfig definition file."""

    root: list[TaskDefinition] = Field(
        default=[], description="The list of configuration tasks to be applied."
    )

    def get_task_definition(self, task_name: str) -> TaskDefinition:
        task = next((x for x in self.root if x.name == task_name), None)
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
