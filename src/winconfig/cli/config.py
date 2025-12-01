from pathlib import Path
from typing import Literal

import yaml
from pydantic import RootModel

from winconfig.cli.execution import Execution
from winconfig.definitions.models.definition import Definition
from winconfig.powershell.process import PowershellRunspace

type ApplyMode = Literal["apply", "revert"]


class ConfigItem(RootModel):
    root: str

    @property
    def name(self) -> str:
        return self.root


class ConfigFile(RootModel):
    root: list[ConfigItem] = []


class WinConfig:
    config: ConfigFile
    definition: Definition

    def __init__(
        self,
        config_path: str,
        definition_path: str = "src/winconfig/definitions/winconfig.definition.yaml",
    ) -> None:
        self.config = ConfigFile.model_validate(
            yaml.safe_load(Path(config_path).read_text())
        )
        self.definition = Definition.model_validate(
            yaml.safe_load(Path(definition_path).read_text())
        )

    def apply(self, mode: ApplyMode) -> None:
        executions = self.generate_executions(mode)
        powershell = PowershellRunspace(preload=self.definition.preload)
        results = [powershell.run(execution.script) for execution in executions]  # noqa: F841

    def generate_executions(self, mode: ApplyMode) -> list[Execution]:
        executions = [
            Execution.generate(
                task_definition=self.definition.get_task_definition(config.name),
                revert=self._resolve_revert(mode),
            )
            for config in self.config.root
        ]
        return executions

    def _resolve_revert(self, mode: ApplyMode) -> bool:
        match mode:
            case "apply":
                return False
            case "revert":
                return True
