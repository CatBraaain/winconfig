from textwrap import dedent

from pydantic import (
    BaseModel,
    Field,
)

from .mode import ApplyMode


class ScriptDefinition(BaseModel):
    """Represents PowerShell scripts to be executed."""

    apply: str | None = Field(
        description="The script to run for the desired configuration."
    )
    revert: str | None = Field(
        description="The script to run for the default configuration."
    )

    def resolve_value(self, mode: ApplyMode) -> str | None:
        return self.apply if mode == "apply" else self.revert

    def generate_custom_script(self, mode: ApplyMode) -> str:
        script = self.resolve_value(mode) or ""
        return dedent(script)
