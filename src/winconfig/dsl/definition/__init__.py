from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
)

from winconfig.dsl.task_plan import TaskMode

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


class TaskDefinitionBody(BaseModel):
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


class TaskDefinition(TaskDefinitionBody):
    name: str = Field(description="The name of the task.")

    def generate_script(self, mode: TaskMode) -> str:
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


class Definition(RootModel):
    """The root model for a winconfig definition file."""

    root: dict[str, TaskDefinitionBody] = Field(
        default={}, description="The list of configuration tasks to be applied."
    )

    def get_task_definition(self, task_name: str) -> TaskDefinition:
        td_body = self.root.get(task_name)
        if td_body is None:
            raise ValueError(f"Task definition {task_name} not found")
        return TaskDefinition.model_validate(
            {"name": task_name, **td_body.model_dump()}
        )
