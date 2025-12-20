from pydantic import BaseModel

from winconfig.config.action import ActionMode, ExecutableActionMode
from winconfig.config.definition import (
    DefinitionBody,
    DefinitionGroupName,
    DefinitionName,
)


class TaskGroup(BaseModel):
    name: str
    tasks: list["Task"]


class Task(DefinitionBody):
    group_name: DefinitionGroupName
    name: DefinitionName
    mode: ActionMode | None

    @property
    def full_name(self) -> str:
        return f"{self.group_name} > {self.name}"

    def generate_script(self, mode: ExecutableActionMode) -> str:
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
