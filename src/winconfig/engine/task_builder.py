from pathlib import Path

import typer
import yaml
from pydantic import RootModel, ValidationError
from yaml import YAMLError

from winconfig.dsl.definition import Definition, TaskMode

from .powershell import PowershellRunspace


class TaskPlan(RootModel):
    root: dict[str, TaskMode] = {}


class TaskBuilder:
    definition: Definition
    plan: TaskPlan

    def __init__(
        self,
        task_plan_path: Path,
        extra_definition_paths: list[Path],
    ) -> None:
        self.definition = self.load_definitions(extra_definition_paths)
        self.plan = self.load_task_plan(task_plan_path)

    def load_definitions(self, extra_definition_paths: list[Path]) -> Definition:
        builtin_definition_path = (
            Path(__file__).parent.parent / "resources" / "builtin.definition.yaml"
        )
        definition_paths = [builtin_definition_path, *extra_definition_paths]
        definitions = [
            self.load_definition(definition_path)
            for definition_path in definition_paths
        ]
        merged_definition = Definition.model_validate(
            [td for d in definitions for td in d.root]
        )
        return merged_definition

    def load_definition(
        self,
        definition_path: Path,
    ) -> Definition:
        try:
            return Definition.model_validate(
                yaml.safe_load(definition_path.read_text())
            )
        except YAMLError:
            typer.echo(f"file {definition_path} is invalid as yaml", err=True)
            raise typer.Exit(1) from None
        except ValidationError:
            typer.echo(f"file {definition_path} is invalid as task plan", err=True)
            raise typer.Exit(1) from None

    def load_task_plan(
        self,
        task_plan_path: Path,
    ) -> TaskPlan:
        try:
            return TaskPlan.model_validate(yaml.safe_load(task_plan_path.read_text()))
        except YAMLError as e:
            typer.echo(f"file {task_plan_path} is not valid as yaml: {e}", err=True)
            raise typer.Exit(1) from None
        except ValidationError as e:
            typer.echo(
                f"file {task_plan_path} is not valid as task plan: {e}", err=True
            )
            raise typer.Exit(1) from None

    def apply(self) -> None:
        powershell = PowershellRunspace()
        for task_name, mode in self.plan.root.items():
            task_definition = self.definition.get_task_definition(task_name)
            script = task_definition.generate_script(mode)
            powershell.run(script)
