from pathlib import Path

from winconfig.dsl.definition import Definition
from winconfig.dsl.task_plan import TaskPlan

from .model_loader import ModelLoader
from .powershell import PowershellRunspace


class TaskBuilder:
    definition: Definition
    plan: TaskPlan

    def __init__(
        self,
        task_plan_path: Path,
        extra_definition_paths: list[Path],
    ) -> None:
        self.definition = ModelLoader.load_definitions(extra_definition_paths)
        self.plan = ModelLoader.load_task_plan(
            task_plan_path=task_plan_path,
            available_definition=self.definition,
        )

    def apply(self) -> None:
        powershell = PowershellRunspace()
        for task_name, mode in self.plan.root.items():
            task_definition = self.definition.get_task_definition(task_name)
            script = task_definition.generate_script(mode)
            powershell.run(script)
