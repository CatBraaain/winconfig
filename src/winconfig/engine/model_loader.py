from pathlib import Path

import yaml
from pydantic import BaseModel, ValidationError
from yaml import YAMLError

from winconfig.dsl.action import ActionConfig
from winconfig.dsl.config import Config
from winconfig.dsl.definition import DefinitionConfig
from winconfig.resources import BUILTIN_DEFINITION_PATH


class ModelLoader:
    @classmethod
    def load_yaml[T: BaseModel](cls, file_path: Path, model_type: type[T]) -> T:
        try:
            return model_type.model_validate(yaml.safe_load(file_path.read_text()))
        except YAMLError:
            raise Exception(f"file {file_path} is invalid as yaml") from None
        except ValidationError:
            raise Exception(
                f"file {file_path} is invalid as {model_type.__name__}"
            ) from None

    @classmethod
    def load_configs(cls, config_paths: list[Path]) -> Config:
        config_paths = [BUILTIN_DEFINITION_PATH, *config_paths]
        configs = [cls.load_yaml(config_path, Config) for config_path in config_paths]

        merged_config = Config(
            Definitions=DefinitionConfig.merge(
                [config.definition_config for config in configs]
            ),
            Actions=ActionConfig.merge([config.action_config for config in configs]),
        )

        for action_group in merged_config.action_config.groups:
            for action in action_group.actions:
                _ = merged_config.definition_config.get_definition(
                    action.group_name, action.name
                )

        return merged_config
