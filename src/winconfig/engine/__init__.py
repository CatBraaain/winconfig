from pathlib import Path

from loguru import logger
from pydantic import BaseModel

from winconfig.dsl.action import ActionMode, ExecutableActionMode
from winconfig.dsl.config import Config
from winconfig.dsl.definition import (
    DefinitionBody,
    DefinitionGroupName,
    DefinitionName,
)
from winconfig.protocol.state_codes import PERMISSION_DENIED
from winconfig.resources import BUILTIN_DEFINITION_PATH

from .model_loader import ModelLoader
from .powershell import PowershellRunspace


class Engine:
    config: Config

    def __init__(self, *config_paths: Path, validate: bool = True) -> None:
        self.config = Config()
        self.merge_config(BUILTIN_DEFINITION_PATH)
        self.merge_config(*config_paths)

        if validate:
            self.config.validate_action_config()

    def merge_config(self, *config_paths: Path) -> None:
        self.config = Config.merge(
            [
                self.config,
                *[ModelLoader.load_config(config_path) for config_path in config_paths],
            ]
        )

    @property
    def groups(self) -> list["TaskGroup"]:
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

        for task_group in self.groups:
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


class TaskGroup(BaseModel):
    name: str
    tasks: list["Task"]


class Task(DefinitionBody):
    group_name: DefinitionGroupName
    name: DefinitionName
    mode: ActionMode | None

    @property
    def full_name(self) -> str:
        return f"{self.group_name} > {self.name}"

    def generate_script(self, mode: ExecutableActionMode) -> str:
        script = "\n".join(
            [
                e.generate_set_script(mode)
                for e in (
                    [
                        registry_item
                        for registry_path in self.registries
                        for registry_item in registry_path.items
                    ]
                    + self.scheduled_tasks
                    + self.services
                    + [self.script]
                )
            ]
        )
        return script
