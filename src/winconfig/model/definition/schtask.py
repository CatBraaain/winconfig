from pathlib import Path
from typing import Literal

from pydantic import (
    BaseModel,
    Field,
)

type SchtaskState = Literal["Enabled", "Disabled"]


class SchtaskDefinition(BaseModel):
    """Represents a scheduled task to be enabled or disabled."""

    full_path: str = Field(description="The full path of the scheduled task.")
    old_state: SchtaskState = Field(
        description="The default state of the scheduled task."
    )
    new_state: SchtaskState = Field(
        description="The desired state of the scheduled task."
    )

    def resolve_value(self, revert: bool) -> str:
        return self.new_state if not revert else self.old_state

    @property
    def formatted_path(self) -> str:
        return "\\" + self.full_path.removeprefix("\\")

    @property
    def path(self) -> str:
        return str(Path(self.formatted_path).parent.as_posix()) + "/"

    @property
    def name(self) -> str:
        return Path(self.formatted_path).name
