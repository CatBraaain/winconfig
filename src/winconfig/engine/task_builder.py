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
        definition_path: str = "src/winconfig/resources/builtin.definition.yaml",
    ) -> None:
        self.plan = TaskPlan.model_validate(yaml.safe_load(Path(plan_path).read_text()))
        self.definition = Definition.model_validate(
            yaml.safe_load(Path(definition_path).read_text())
        )

    def apply(self) -> None:
        powershell = PowershellRunspace()
        for task_name, mode in self.plan.root.items():
            task_definition = self.definition.get_task_definition(task_name)
            script = task_definition.generate_script(mode)
            powershell.run(script)
