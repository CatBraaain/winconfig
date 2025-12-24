from pathlib import Path
from typing import Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from yaml import YAMLError

from winconfig.exceptions import (
    ConfigValidationError,
    ConfigYamlError,
    DefinitionGroupNotFoundError,
    DefinitionNotFoundError,
)

from .action import ActionConfig, ActionMode
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
            raise ConfigYamlError(file_path) from None
        except ValidationError:
            raise ConfigValidationError(file_path) from None

    def merge_from_yaml(self, *config_paths: Path) -> Self:
        configs = [Config.from_yaml(config_path) for config_path in config_paths]
        self.definition_config.merge([config.definition_config for config in configs])
        self.action_config.merge([config.action_config for config in configs])
        return self

    def validate_action_config(self) -> None:
        for action_group_name, action_group in self.action_config.root.items():
            if action_group_name not in self.definition_config.root:
                raise DefinitionGroupNotFoundError(action_group_name)
            for action_name in action_group:
                if action_name not in self.definition_config.root[action_group_name]:
                    raise DefinitionNotFoundError(action_group_name, action_name)

        for def_group_name, def_group in self.definition_config.root.items():
            if def_group_name not in self.action_config.root:
                self.action_config.root[def_group_name] = {}
            for definition_name in def_group:
                if definition_name not in self.action_config.root[def_group_name]:
                    self.action_config.root[def_group_name][definition_name] = (
                        ActionMode.SKIP
                    )
