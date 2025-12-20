from pathlib import Path
from typing import Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from yaml import YAMLError

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
    def from_yaml(cls, file_path: Path) -> Self:
        try:
            return cls.model_validate(yaml.safe_load(file_path.read_text()))
        except YAMLError:
            raise Exception(f"file {file_path} is invalid as yaml") from None
        except ValidationError:
            raise Exception(f"file {file_path} is invalid as {cls.__name__}") from None

    def merge(self, *config_paths: Path) -> None:
        configs = [Config.from_yaml(config_path) for config_path in config_paths]
        self.definition_config.merge([config.definition_config for config in configs])
        self.action_config.merge([config.action_config for config in configs])

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
