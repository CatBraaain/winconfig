from pathlib import Path

import yaml
from pydantic import RootModel

from winconfig.definitions.builtin_taskname import TaskName
from winconfig.models.definition import Definition, TaskMode

from .process import PowershellRunspace


class ConfigFile(RootModel):
    root: dict[TaskName, TaskMode] = {}


class WinConfig:
    config: ConfigFile
    definition: Definition

    def __init__(
        self,
        config_path: str,
        definition_path: str = "src/winconfig/definitions/builtin.definition.yaml",
    ) -> None:
        self.config = ConfigFile.model_validate(
            yaml.safe_load(Path(config_path).read_text())
        )
        self.definition = Definition.model_validate(
            yaml.safe_load(Path(definition_path).read_text())
        )

    def apply(self) -> None:
        powershell = PowershellRunspace()
        for task_name, mode in self.config.root.items():
            task_definition = self.definition.get_task_definition(task_name)
            script = task_definition.generate_script(mode)
            powershell.run(script)
