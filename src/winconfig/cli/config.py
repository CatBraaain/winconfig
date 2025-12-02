from pathlib import Path

import yaml
from pydantic import RootModel

from winconfig.models.definition import ApplyMode, Definition

from .process import PowershellRunspace


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
        for config in self.config.root:
            task_definition = self.definition.get_task_definition(config.name)
            script = task_definition.generate_script(mode)
            powershell.run(script)
