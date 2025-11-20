from typing import Self

from pydantic import BaseModel

from winconfig.powershell.script_generator import ScriptGenerator

from .definition.definition import TaskDefinition


class Execution(BaseModel):
    name: str
    revert: bool
    script: str

    @classmethod
    def from_definition(cls, task_definition: TaskDefinition, revert: bool) -> Self:
        return cls(
            name=task_definition.name,
            revert=revert,
            script=ScriptGenerator.generate_execution(task_definition, revert),
        )
