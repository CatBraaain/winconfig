from pydantic import BaseModel, ConfigDict, Field

from .action import ActionCollection
from .definition import DefinitionCollection


class Config(BaseModel):
    definition_collection: DefinitionCollection = Field(
        default=DefinitionCollection(),
        alias="Definitions",
    )
    action_collection: ActionCollection = Field(
        default=ActionCollection(),
        alias="Actions",
    )

    model_config = ConfigDict(
        extra="forbid",
        validate_by_name=True,
        validate_by_alias=True,
    )
