from typing import Self

from pydantic import BaseModel, ConfigDict, Field

from .action import ActionConfig
from .definition import DefinitionConfig


class Config(BaseModel):
    definition_config: DefinitionConfig = Field(
        default=DefinitionConfig(),
        alias="Definitions",
    )
    action_config: ActionConfig = Field(
        default=ActionConfig(),
        alias="Actions",
    )

    model_config = ConfigDict(
        extra="forbid",
        validate_by_name=True,
        validate_by_alias=True,
    )

    @classmethod
    def merge(cls, configs: list[Self]) -> Self:
        return cls(
            Definitions=DefinitionConfig.merge(
                [config.definition_config for config in configs]
            ),
            Actions=ActionConfig.merge([config.action_config for config in configs]),
        )

    def validate_action_config(self) -> None:
        for action_group in self.action_config.groups:
            for action in action_group.actions:
                _ = self.definition_config.get_definition(
                    action.group_name, action.name
                )
