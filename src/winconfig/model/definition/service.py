from typing import Literal

from pydantic import (
    BaseModel,
    Field,
)

type ServiceStartupType = Literal[
    "Automatic",
    "AutomaticDelayedStart",
    "Disabled",
    "InvalidValue",
    "Manual",
]


class ServiceDefinition(BaseModel):
    """Represents a Windows service to be modified."""

    name: str = Field(description="The name of the service.")
    old_startup: ServiceStartupType = Field(
        description="The default startup type of the service."
    )
    new_startup: ServiceStartupType = Field(
        description="The desired startup type of the service."
    )

    def resolve_value(self, revert: bool) -> str:
        return self.new_startup if not revert else self.old_startup
