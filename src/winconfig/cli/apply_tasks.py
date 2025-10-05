import re
import subprocess

from winconfig.model.task import Task

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


def apply_tasks(tasks: list[Task]) -> str:
    ps_args = ", ".join(
        f'"{re.sub(r'(["$])', r"`\1", task.script_code)}"' for task in tasks
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
