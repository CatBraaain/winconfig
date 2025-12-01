from typing import Self

from pydantic import BaseModel

from winconfig.models.definition import TaskDefinition


class Execution(BaseModel):
    name: str
    revert: bool
    script: str

    @classmethod
    def generate(cls, task_definition: TaskDefinition, revert: bool) -> Self:
        script = "\n".join(
            [
                registry.generate_set_script(revert)
                for registry in task_definition.registries
            ]
            + [
                task.generate_set_script(revert)
                for task in task_definition.scheduled_tasks
            ]
            + [
                service.generate_set_script(revert)
                for service in task_definition.services
            ]
            + [task_definition.script.generate_custom_script(revert)]
        )
        return cls(
            name=task_definition.name,
            revert=revert,
            script=script,
        )
