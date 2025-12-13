from pathlib import Path

from loguru import logger

from winconfig.dsl.config import Config
from winconfig.dsl.definition import PERMISSION_DENIED

from .model_loader import ModelLoader
from .powershell import PowershellRunspace


class TaskBuilder:
    config: Config

    def __init__(
        self,
        config_path: Path,
    ) -> None:
        self.config = ModelLoader.load_config([config_path])

    def apply(self, reverse: bool) -> None:
        powershell = PowershellRunspace()
        logger.debug(f"Setup PowerShell: version {powershell.runspace.Version}")

        for action_group in self.config.action_config.groups:
            for action in action_group.actions:
                definition = self.config.definition_config.get_definition(
                    action.group_name, action.name
                )
                action_mode = action.mode.resolve(reverse)
                script = definition.generate_script(action_mode).strip()
                try:
                    stdout = powershell.run(script)
                    logger.info(f"Success: {definition.full_name}[{action_mode.value}]")
                    if PERMISSION_DENIED in stdout:
                        raise Exception(
                            "Administrator privileges required for this operation"
                        )
                except Exception as e:
                    logger.error(
                        f"Fail: {definition.full_name}[{action_mode.value}]: {e}"
                    )
                    raise
                finally:
                    logger.debug(
                        f"{definition.full_name}[{action_mode.value}]:\n```powershell\n{script}\n```"
                    )
