from pathlib import Path
from typing import Literal

import yaml

from winconfig.model.config import ConfigContainer
from winconfig.model.definition.definition import Definition
from winconfig.model.execution import Execution
from winconfig.powershell.process import PowershellRunspace

type ApplyMode = Literal["apply", "revert"]


class ConfigApplier:
    config_path: str
    definition_path: str

    config_container: ConfigContainer
    definition: Definition

    def __init__(
        self,
        config_path: str,
        definition_path: str = "src/winconfig/definitions/winconfig.definition.yaml",
    ) -> None:
        self.config_path = config_path
        self.definition_path = definition_path
        self.config_container = ConfigContainer.model_validate(
            yaml.safe_load(Path(self.config_path).read_text())
        )
        self.definition = Definition.model_validate(
            yaml.safe_load(Path(self.definition_path).read_text())
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
            for config in self.config_container.root
        ]
        return executions

    def _resolve_revert(self, mode: ApplyMode) -> bool:
        match mode:
            case "apply":
                return False
            case "revert":
                return True
