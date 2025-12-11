from pathlib import Path

import yaml
from pydantic import BaseModel, ValidationError
from yaml import YAMLError

from winconfig.dsl.definition import Definition
from winconfig.dsl.task_plan import TaskPlan
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
    def load_definitions(cls, extra_definition_paths: list[Path]) -> Definition:
        definition_paths = [BUILTIN_DEFINITION_PATH, *extra_definition_paths]
        definitions = [
            cls.load_yaml(definition_path, Definition)
            for definition_path in definition_paths
        ]
        merged_definition = Definition.model_validate(
            {
                name: body
                for definition in definitions
                for name, body in definition.root.items()
            }
        )
        return merged_definition

    @classmethod
    def load_task_plan(
        cls, task_plan_path: Path, available_definition: Definition | None = None
    ) -> TaskPlan:
        task_plan = cls.load_yaml(task_plan_path, TaskPlan)

        if available_definition is None:
            available_definition = cls.load_definitions([])

        for task_name in task_plan.root:
            if task_name not in available_definition.root:
                raise Exception(f"task {task_name} not found in definition")

        return task_plan
