from typing import Self

from pydantic import BaseModel, ConfigDict, Field

from .action import ActionConfig
from .definition import DefinitionConfig


class Config(BaseModel):
    """The root model for a winconfig definition file."""

    definition_config: DefinitionConfig = Field(
        default=DefinitionConfig(),
        alias="Definitions",
        description="Task definition entries.",
    )
    action_config: ActionConfig = Field(
        default=ActionConfig(),
        alias="Actions",
        description="Task action entries to be executed.",
    )

    model_config = ConfigDict(
        extra="forbid",
        validate_by_name=True,
        validate_by_alias=True,
    )

    @classmethod
    def merge(cls, configs: list[Self]) -> Self:
        return cls(
            definition_config=DefinitionConfig.merge(
                [config.definition_config for config in configs]
            ),
            action_config=ActionConfig.merge(
                [config.action_config for config in configs]
            ),
        )

    def validate_action_config(self) -> None:
        for action_group_name, action_group in self.action_config.root.items():
            for action_name in action_group:
                definition_group = self.definition_config.root.get(action_group_name)
                if definition_group is None:
                    raise ValueError(
                        f'Definition Group "{action_group_name}" not found'
                    )
                definition_body = definition_group.get(action_name)
                if definition_body is None:
                    raise ValueError(
                        f'Definition "{action_name}" not found in Definition Group "{action_group_name}"'
                    )
