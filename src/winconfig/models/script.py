from textwrap import dedent

from pydantic import (
    BaseModel,
    Field,
)

from .const_types import ApplyMode, TaskMode


class ScriptDefinition(BaseModel):
    """Represents PowerShell scripts to be executed."""

    apply: str | None = Field(
        description="The script to run for the desired configuration."
    )
    revert: str | None = Field(
        description="The script to run for the default configuration."
    )

    def resolve_value(self, mode: ApplyMode) -> str:
        match mode:
            case TaskMode.APPLY:
                return self.apply or ""
            case TaskMode.REVERT:
                return self.revert or ""
            case _:
                raise ValueError(f"Invalid mode: {mode}")

    def generate_custom_script(self, mode: TaskMode) -> str:
        if mode == TaskMode.SKIP:
            return ""
        return dedent(self.resolve_value(mode))
