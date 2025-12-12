from textwrap import dedent

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from winconfig.dsl.action import ActionMode, ApplyMode


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

    def resolve_value(self, mode: ApplyMode) -> str:
        match mode:
            case ActionMode.APPLY:
                return self.apply
            case ActionMode.REVERT:
                return self.revert
            case _:
                raise ValueError(f"Invalid mode: {mode}")

    def generate_set_script(self, mode: ActionMode) -> str:
        if mode == ActionMode.SKIP:
            return ""
        return dedent(self.resolve_value(mode))
