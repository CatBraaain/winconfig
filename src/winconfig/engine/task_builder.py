from pathlib import Path

import yaml
from pydantic import RootModel

from winconfig.dsl.definition import Definition, TaskMode

from .powershell import PowershellRunspace


class TaskPlan(RootModel):
    root: dict[str, TaskMode] = {}


class TaskBuilder:
    plan: TaskPlan
    definition: Definition

    def __init__(
        self,
        plan_path: str,
        extra_definition_paths: list[str],
    ) -> None:
        self.plan = TaskPlan.model_validate(yaml.safe_load(Path(plan_path).read_text()))
        self.definition = self.load_definitions(extra_definition_paths)

    def load_definitions(
        self,
        additional_definition_paths: list[str],
    ) -> Definition:
        builtin_definition_path = str(
            Path(__file__).parent.parent / "resources" / "builtin.definition.yaml"
        )
        definition_paths = [builtin_definition_path, *additional_definition_paths]
        definitions = [
            Definition.model_validate(yaml.safe_load(Path(definition_path).read_text()))
            for definition_path in definition_paths
        ]
        all_task_definitions = [td for d in definitions for td in d.root]
        return Definition.model_validate(all_task_definitions)

    def apply(self) -> None:
        powershell = PowershellRunspace()
        for task_name, mode in self.plan.root.items():
            task_definition = self.definition.get_task_definition(task_name)
            script = task_definition.generate_script(mode)
            powershell.run(script)
