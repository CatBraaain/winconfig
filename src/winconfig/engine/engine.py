from pathlib import Path

from loguru import logger

from winconfig.config.action import ActionMode
from winconfig.config.config import Config
from winconfig.exceptions import TaskError
from winconfig.resources import BUILTIN_DEFINITION_PATH

from .powershell import PowershellRunspace
from .task import Task, TaskGroup


class Engine:
    config: Config

    def __init__(self, *config_paths: Path, validate: bool = True) -> None:
        self.config = Config.from_yaml(BUILTIN_DEFINITION_PATH).merge_from_yaml(
            *config_paths
        )

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

    def run(self, *, reverse: bool) -> None:
        powershell = PowershellRunspace()
        logger.debug(f"Setup PowerShell: version {powershell.runspace.Version}")

        for task_group in self.task_groups:
            for task in task_group.tasks:
                if task.mode is None:
                    logger.debug(f"NoAction: {task.full_name}")
                    continue
                action_mode = task.mode.resolve(reverse=reverse)
                if action_mode == ActionMode.SKIP:
                    logger.info(f"Skipped: {task.full_name}[{action_mode}]")
                    continue
                script = task.generate_script(action_mode).strip()
                try:
                    powershell.run(script)
                    logger.info(f"Success: {task.full_name}[{action_mode}]")
                    logger.debug(
                        f"{task.full_name}[{action_mode}]:\n```powershell\n{script}\n```"
                    )
                except Exception as e:
                    raise TaskError(
                        task_name=task.full_name,
                        action_mode=action_mode,
                        script=script,
                        exception=e,
                    ) from e
