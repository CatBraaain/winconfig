from pathlib import Path
from typing import Literal

import yaml
from pydantic import RootModel

from winconfig.models.definition import Definition
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
        powershell = PowershellRunspace()
        should_revert = self._resolve_revert(mode)
        for config in self.config.root:
            task_definition = self.definition.get_task_definition(config.name)
            script = task_definition.generate_script(revert=should_revert)
            powershell.run(script)

    def _resolve_revert(self, mode: ApplyMode) -> bool:
        match mode:
            case "apply":
                return False
            case "revert":
                return True
