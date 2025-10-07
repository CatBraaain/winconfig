from typing import Self

from pydantic import BaseModel

from .definition import Definition


class Task(BaseModel):
    name: str
    revert: bool
    execution_script: str

    @classmethod
    def from_definition(cls, definition: Definition, revert: bool) -> Self:
        execution_script = "\n".join(
            e.generate_execution_script(revert)
            for e in (
                definition.registries
                + definition.scheduled_tasks
                + definition.services
                + [definition.script]
            )
        )
        return cls(
            name=definition.name, revert=revert, execution_script=execution_script
        )
