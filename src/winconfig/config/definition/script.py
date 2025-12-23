from textwrap import dedent
from typing import assert_never

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from winconfig.config.action import ActionMode, ExecutableActionMode


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

    model_config = ConfigDict(extra="forbid")

    def resolve_value(self, mode: ExecutableActionMode) -> str:
        match mode:
            case ActionMode.APPLY:
                return self.apply
            case ActionMode.REVERT:
                return self.revert
            case _:
                assert_never(mode)

    def generate_set_script(self, mode: ExecutableActionMode) -> str:
        return dedent(self.resolve_value(mode))
