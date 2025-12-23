# from winconfig.exceptions import TaskError
from pathlib import Path


class PowerShellError(Exception):
    pass


class PowerShellAdminRequiredError(PowerShellError):
    def __init__(self) -> None:
        super().__init__("Administrator privileges required for this operation")


class TaskError(Exception):
    def __init__(
        self, task_name: str, action_mode: str, script: str, exception: Exception
    ) -> None:
        super().__init__(
            f"Failed: {task_name}[{action_mode}]: {exception}\n```powershell\n{script}\n```"
        )


class ConfigError(Exception):
    pass


class ConfigYamlError(ConfigError):
    def __init__(self, path: Path) -> None:
        super().__init__(f'file "{path}" is invalid as yaml')


class ConfigValidationError(ConfigError):
    def __init__(self, path: Path) -> None:
        super().__init__(f'file "{path}" is invalid as config')


class ActionConfigValidationError(ConfigError):
    pass


class DefinitionGroupNotFoundError(ActionConfigValidationError):
    def __init__(self, group_name: str) -> None:
        super().__init__(f'Definition Group "{group_name}" not found')


class DefinitionNotFoundError(ActionConfigValidationError):
    def __init__(self, group_name: str, action_name: str) -> None:
        super().__init__(
            f'Definition "{action_name}" not found in Definition Group "{group_name}"'
        )
