import re
import subprocess
from pathlib import Path
from typing import Literal

import yaml

from winconfig.model.config import Config, ConfigContainer
from winconfig.model.definition import DefinitionContainer
from winconfig.model.task import Task

RUNSPACE_POOL_TEMPLATE = r"""
param([string[]]$Scripts)

$pool = [runspacefactory]::CreateRunspacePool(1, 4)
$pool.Open()

$jobs = @()
$Scripts | % {
    $ps = [PowerShell]::Create()
    $ps.RunspacePool = $pool
    $ps.AddScript($_) | Out-Null
    $jobs += [PSCustomObject]@{
        PowerShell  = $ps
        AsyncResult = $ps.BeginInvoke()
    }
}

$results = $jobs | % {
    $ps = $_.PowerShell
    $result = $ps.EndInvoke($_.AsyncResult)
    $ps.Dispose()
    return $result
}

$pool.Close()
$pool.Dispose()

"""

type ApplyMode = Literal["apply", "revert", "auto"]


class ConfigApplier:
    config_path: str
    definition_path: str

    def __init__(
        self,
        config_path: str,
        definition_path: str = "src/winconfig/definitions/winutil_definitions.yaml",
    ) -> None:
        self.config_path = config_path
        self.definition_path = definition_path

    def apply(self, mode: ApplyMode) -> None:
        tasks = self.generate_tasks(mode)
        self.execute_tasks(tasks)

    def generate_tasks(self, mode: ApplyMode) -> list[Task]:
        config_container = ConfigContainer.model_validate(
            yaml.safe_load(Path(self.config_path).read_text())
        )
        definition_container = DefinitionContainer.model_validate(
            yaml.safe_load(Path(self.definition_path).read_text())
        )
        tasks = [
            Task.from_definition(
                definition=definition_container.get_definition(config.name),
                revert=self._resolve_revert(mode, config),
            )
            for config in config_container.root
        ]
        return tasks

    def _resolve_revert(self, mode: ApplyMode, config: Config) -> bool:
        match mode:
            case "apply":
                return False
            case "revert":
                return True
            case "auto":
                return config.revert

    def execute_tasks(self, tasks: list[Task]) -> str:
        ps_args = ", ".join(
            f'"{re.sub(r'(["$])', r"`\1", task.execution_script)}"' for task in tasks
        )
        cmd = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            f"& {{ {RUNSPACE_POOL_TEMPLATE} }} -Scripts @({ps_args})",
        ]
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        return result.stdout + "\n" + result.stderr
