from typing import Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
)

from .registry import RegistryPathDefinition
from .schtask import SchtaskDefinition
from .script import ScriptDefinition
from .service import ServiceDefinition


class DefinitionBody(BaseModel):
    """A single, self-contained configuration task."""

    description: str = Field(description="A description of the task's purpose.")
    registries: list[RegistryPathDefinition] = Field(
        default=[],
        description="The registry values to be modified.",
    )
    scheduled_tasks: list[SchtaskDefinition] = Field(
        default=[],
        description="The scheduled tasks to be modified.",
    )
    services: list[ServiceDefinition] = Field(
        default=[],
        description="The Windows services to be modified.",
    )
    script: ScriptDefinition = Field(
        default=ScriptDefinition(),
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


type DefinitionGroupName = str
type DefinitionName = str


class DefinitionConfig(RootModel):
    root: dict[DefinitionGroupName, dict[DefinitionName, DefinitionBody]] = {}

    def merge(self, definition_configs: list[Self]) -> None:
        merged: dict[DefinitionGroupName, dict[DefinitionName, DefinitionBody]] = (
            self.root.copy()
        )
        for definition_config in definition_configs:
            for group_name, group in definition_config.root.items():
                if group_name not in merged:
                    merged[group_name] = {}
                merged[group_name] |= group

        validated = self.model_validate(merged)
        self.root = validated.root
