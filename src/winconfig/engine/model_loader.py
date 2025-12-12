from pathlib import Path

import yaml
from pydantic import BaseModel, ValidationError
from yaml import YAMLError

from winconfig.dsl.config import Config
from winconfig.dsl.definition import Definition, TaskDefinitionBody
from winconfig.dsl.task_plan import TaskMode, TaskPlan
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

        merged_definition: dict[str, dict[str, TaskDefinitionBody]] = {}
        for config in configs:
            for group_name, td_group in config.definition.root.items():
                if group_name not in merged_definition:
                    merged_definition[group_name] = {}
                merged_definition[group_name] |= td_group

        merged_plan: dict[str, dict[str, TaskMode]] = {}
        for config in configs:
            for group_name, task_group in config.plan.root.items():
                if group_name not in merged_plan:
                    merged_plan[group_name] = {}
                merged_plan[group_name] |= task_group

        merged_config = Config.model_validate(
            {
                "definition": Definition.model_validate(merged_definition),
                "plan": TaskPlan.model_validate(merged_plan),
            }
        )

        for task_group_name, task_group in merged_config.plan.root.items():
            for task_name in task_group:
                _ = merged_config.definition.get_task_definition(
                    task_group_name, task_name
                )

        return merged_config
