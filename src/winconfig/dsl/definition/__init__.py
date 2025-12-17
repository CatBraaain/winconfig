from typing import Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
)

from .const_types import (  # noqa: F401
    ACCESS_DENIED,
    EXIST,
    NOT_CHANGE,
    NOT_EXIST,
    PERMISSION_DENIED,
)
from .registry import (  # noqa: F401
    RegistryEntryDefinition,
    RegistryPathDefinition,
    RegistryValueKind,
)
from .schtask import SchtaskDefinition, SchtaskState  # noqa: F401
from .script import ScriptDefinition
from .service import ServiceDefinition, ServiceStartupType  # noqa: F401


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
type DefinitionGroupDict = dict[DefinitionName, DefinitionBody]
type DefinitionName = str
type DefinitionCollectionRoot = dict[DefinitionGroupName, DefinitionGroupDict]


class DefinitionConfig(RootModel):
    """The root model for a winconfig definition file."""

    root: DefinitionCollectionRoot = Field(
        default={}, description="The list of configuration tasks to be applied."
    )

    @classmethod
    def merge(cls, definition_configs: list[Self]) -> Self:
        merged: DefinitionCollectionRoot = {}
        for definition_config in definition_configs:
            for group_name, group in definition_config.root.items():
                if group_name not in merged:
                    merged[group_name] = {}
                merged[group_name] |= group

        return cls.model_validate(merged)
