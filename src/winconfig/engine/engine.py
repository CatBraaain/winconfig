from pathlib import Path

from loguru import logger

from winconfig.config.action import ActionMode
from winconfig.config.config import Config
from winconfig.protocol.state_codes import PERMISSION_DENIED
from winconfig.resources import BUILTIN_DEFINITION_PATH

from .powershell import PowershellRunspace
from .task import Task, TaskGroup


class Engine:
    config: Config

    def __init__(self, *config_paths: Path, validate: bool = True) -> None:
        self.config = Config()
        self.config.merge(BUILTIN_DEFINITION_PATH)
        self.config.merge(*config_paths)

        if validate:
            self.config.validate_action_config()

    @property
    def task_groups(self) -> list["TaskGroup"]:
        return [
            TaskGroup(
                name=definition_group_name,
                tasks=[
                    Task(
                        group_name=definition_group_name,
                        name=definition_name,
                        mode=(
                            self.config.action_config.root.get(
                                definition_group_name, {}
                            ).get(definition_name, None)
                        ),
                        **definition_body.model_dump(),
                    )
                    for definition_name, definition_body in definition_group.items()
                ],
            )
            for definition_group_name, definition_group in self.config.definition_config.root.items()
        ]

    def run(self, reverse: bool) -> None:
        powershell = PowershellRunspace()
        logger.debug(f"Setup PowerShell: version {powershell.runspace.Version}")

        for task_group in self.task_groups:
            for task in task_group.tasks:
                if task.mode is None:
                    logger.debug(f"NoAction: {task.full_name}")
                    continue
                action_mode = task.mode.resolve(reverse)
                if action_mode == ActionMode.SKIP:
                    logger.info(f"Skipped: {task.full_name}[{action_mode}]")
                    continue
                script = task.generate_script(action_mode).strip()
                try:
                    stdout = powershell.run(script)
                    logger.info(f"Success: {task.full_name}[{action_mode}]")
                    if PERMISSION_DENIED in stdout:
                        raise Exception(
                            "Administrator privileges required for this operation"
                        )
                except Exception as e:
                    raise Exception(
                        f"Failed: {task.full_name}[{action_mode}]: {e}"
                    ) from e
                finally:
                    logger.debug(
                        f"{task.full_name}[{action_mode}]:\n```powershell\n{script}\n```"
                    )
