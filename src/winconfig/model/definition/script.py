from pydantic import (
    BaseModel,
    Field,
)


class ScriptDefinition(BaseModel):
    """Represents PowerShell scripts to be executed."""

    apply: str | None = Field(
        description="The script to run for the desired configuration."
    )
    revert: str | None = Field(
        description="The script to run for the default configuration."
    )

    def resolve_value(self, revert: bool) -> str | None:
        return self.apply if not revert else self.revert
