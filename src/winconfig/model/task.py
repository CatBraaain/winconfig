from typing import Self

from pydantic import BaseModel

from winconfig.generator.script_generator import ScriptGenerator

from .definition import Definition


class Task(BaseModel):
    name: str
    revert: bool
    execution_script: str

    @classmethod
    def from_definition(cls, definition: Definition, revert: bool) -> Self:
        return cls(
            name=definition.name,
            revert=revert,
            execution_script=ScriptGenerator.generate_script(definition, revert),
        )
