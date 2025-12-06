from textwrap import dedent

from pydantic import (
    BaseModel,
    Field,
)

from winconfig.dsl.task_plan import ApplyMode, TaskMode


class ScriptDefinition(BaseModel):
    """Represents PowerShell scripts to be executed."""

    apply: str = Field(
        default="",
        description="The script to run for the desired configuration.",
    )
    revert: str = Field(
        default="",
        description="The script to run for the default configuration.",
    )

    def resolve_value(self, mode: ApplyMode) -> str:
        match mode:
            case TaskMode.APPLY:
                return self.apply
            case TaskMode.REVERT:
                return self.revert
            case _:
                raise ValueError(f"Invalid mode: {mode}")

    def generate_set_script(self, mode: TaskMode) -> str:
        if mode == TaskMode.SKIP:
            return ""
        return dedent(self.resolve_value(mode))
