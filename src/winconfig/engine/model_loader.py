from pathlib import Path

import yaml
from pydantic import BaseModel, ValidationError
from yaml import YAMLError

from winconfig.dsl.action import (
    ActionCollection,
    ActionCollectionRoot,
)
from winconfig.dsl.config import Config
from winconfig.dsl.definition import (
    DefinitionCollection,
    DefinitionCollectionRoot,
)
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

        merged_definition_collection: DefinitionCollectionRoot = {}
        for config in configs:
            for (
                definition_group_name,
                definition_group,
            ) in config.definition_collection.root.items():
                if definition_group_name not in merged_definition_collection:
                    merged_definition_collection[definition_group_name] = {}
                merged_definition_collection[definition_group_name] |= definition_group

        merged_action_collection: ActionCollectionRoot = {}
        for config in configs:
            for (
                definition_group_name,
                action_group,
            ) in config.action_collection.root.items():
                if definition_group_name not in merged_action_collection:
                    merged_action_collection[definition_group_name] = {}
                merged_action_collection[definition_group_name] |= action_group

        merged_config = Config.model_validate(
            {
                "Definitions": DefinitionCollection.model_validate(
                    merged_definition_collection
                ),
                "Actions": ActionCollection.model_validate(merged_action_collection),
            }
        )

        for (
            task_group_name,
            action_group,
        ) in merged_config.action_collection.root.items():
            for task_name in action_group:
                _ = merged_config.definition_collection.get_definition(
                    task_group_name, task_name
                )

        return merged_config
