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
        self.config = ModelLoader.load_configs([config_path])

    def apply(self, reverse: bool) -> None:
        powershell = PowershellRunspace()
        logger.debug(f"Setup PowerShell: version {powershell.runspace.Version}")

        for task_group_name, task_group in self.config.plan.root.items():
            for task_name, planed_mode in task_group.items():
                td = self.config.definition.get_task_definition(
                    task_group_name, task_name
                )
                mode = planed_mode.resolve(reverse)
                script = td.generate_script(mode).strip()
                try:
                    stdout = powershell.run(script)
                    logger.info(f"Success: {td.full_name}[{mode.value}]")
                    if PERMISSION_DENIED in stdout:
                        raise Exception(
                            "Administrator privileges required for this operation"
                        )
                except Exception as e:
                    logger.error(f"Fail: {td.full_name}[{mode.value}]: {e}")
                    raise
                finally:
                    logger.debug(
                        f"{td.full_name}[{mode.value}]:\n```powershell\n{script}\n```"
                    )
