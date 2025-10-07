import re
import subprocess
from pathlib import Path
from typing import Annotated, Literal

import typer
import yaml

from winconfig.model.config import Config, ConfigContainer
from winconfig.model.definition import DefinitionContainer
from winconfig.model.task import Task

type ApplyMode = Literal["apply", "revert", "auto"]


def apply_config(
    path: Annotated[str, typer.Option()], mode: ApplyMode = "auto"
) -> None:
    config_container = ConfigContainer.model_validate(
        yaml.safe_load(Path(path).read_text())
    )
    definition_container = DefinitionContainer.model_validate(
        yaml.safe_load(
            Path("src/winconfig/definitions/winutil_definitions.yaml").read_text()
        )
    )

    tasks = [
        Task.from_definition(
            definition=definition_container.get_definition(config.name),
            revert=_resolve_revert(mode, config),
        )
        for config in config_container.root
    ]
    result = execute_tasks(tasks)


def _resolve_revert(mode: ApplyMode, config: Config) -> bool:
    match mode:
        case "apply":
            return False
        case "revert":
            return True
        case "auto":
            return config.revert


run_on_runspacepool = r"""
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


def execute_tasks(tasks: list[Task]) -> str:
    ps_args = ", ".join(
        f'"{re.sub(r'(["$])', r"`\1", task.execution_script)}"' for task in tasks
    )
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        f"& {{ {run_on_runspacepool} }} -Scripts @({ps_args})",
    ]
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    return result.stdout + "\n" + result.stderr
