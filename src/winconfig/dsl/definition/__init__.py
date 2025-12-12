from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
)

from winconfig.dsl.action import ActionMode

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


class Definition(DefinitionBody):
    group: str
    name: str

    @property
    def full_name(self) -> str:
        return f"{self.group} - {self.name}"

    def generate_script(self, mode: ActionMode) -> str:
        script = "\n".join(
            [
                e.generate_set_script(mode)
                for e in (
                    [
                        registry_item
                        for registry_path in self.registries
                        for registry_item in registry_path.items
                    ]
                    + self.scheduled_tasks
                    + self.services
                    + [self.script]
                )
            ]
        )
        return script


type DefinitionGroupName = str
type DefinitionGroup = dict[DefinitionName, DefinitionBody]
type DefinitionName = str
type DefinitionCollectionRoot = dict[DefinitionGroupName, DefinitionGroup]


class DefinitionCollection(RootModel):
    """The root model for a winconfig definition file."""

    root: DefinitionCollectionRoot = Field(
        default={}, description="The list of configuration tasks to be applied."
    )

    def get_definition(
        self, definition_group_name: str, definition_name: str
    ) -> Definition:
        definition_group = self.root.get(definition_group_name)
        if definition_group is None:
            raise ValueError(f"Definition group {definition_group_name} not found")
        definition_body = definition_group.get(definition_name)
        if definition_body is None:
            raise ValueError(
                f"Definition {definition_group_name} - {definition_name} not found"
            )
        return Definition.model_validate(
            {
                "name": definition_name,
                "group": definition_group_name,
                **definition_body.model_dump(),
            }
        )
