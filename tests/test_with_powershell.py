import subprocess
from pathlib import Path

import pytest
import yaml

from winconfig.model.definition import DefinitionContainer


def run_powershell_command(command):
    """Executes a PowerShell command and returns the output."""
    try:
        result = subprocess.run(
            ["powershell", "-Command", command],
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"ERROR: {e.stderr.strip()}"
    except FileNotFoundError:
        return "ERROR: powershell.exe not found."


# Load definitions once for all tests
DEFINITIONS_FILE = Path("src/winconfig/definitions/winutil_definitions.yaml")
definition_container = DefinitionContainer.model_validate(
    yaml.safe_load(DEFINITIONS_FILE.read_text())
)
all_definitions = definition_container.root


@pytest.mark.parametrize(
    "definition", all_definitions, ids=[d.name for d in all_definitions]
)
def test_revert_values(definition):
    """
    Tests the revert values for each definition by checking the current system state.
    """
    # Test revert values for registries
    for registry in definition.registries:
        if registry.old_value == "<RemoveEntry>":
            # Check if the registry property does not exist
            ps_command = f"(Get-ItemProperty -Path '{registry.path}' -Name '{registry.name}' -ErrorAction SilentlyContinue) -eq $null"
            current_value = run_powershell_command(ps_command)
            assert current_value.lower() == "true", (
                f"[{definition.name}] Registry '{registry.name}' at '{registry.path}' should be removed, but it exists."
            )
        else:
            # Check if the registry value matches the old_value
            ps_command = f"(Get-ItemProperty -Path '{registry.path}' -Name '{registry.name}' -ErrorAction SilentlyContinue).'{registry.name}'"
            current_value = run_powershell_command(ps_command)
            assert str(current_value) == str(registry.old_value), (
                f"[{definition.name}] Registry '{registry.name}' at '{registry.path}' expected '{registry.old_value}', but got '{current_value}'."
            )

    # Test revert values for services
    for service in definition.services:
        ps_command = f"(Get-Service -Name '{service.name}' -ErrorAction SilentlyContinue).StartType.ToString()"
        current_value = run_powershell_command(ps_command)
        assert current_value == service.old_startup_type, (
            f"[{definition.name}] Service '{service.name}' expected startup type '{service.old_startup_type}', but got '{current_value}'."
        )

    # Test revert values for scheduled tasks
    for task in definition.scheduled_tasks:
        ps_command = f"(Get-ScheduledTask -TaskName '{task.path}' -ErrorAction SilentlyContinue).State.ToString()"
        current_value = run_powershell_command(ps_command)
        expected_state = "Ready" if task.old_state == "Enabled" else "Disabled"
        assert current_value == expected_state, (
            f"[{definition.name}] Scheduled Task '{task.path}' expected state '{expected_state}', but got '{current_value}'."
        )

    # Note: Testing 'script' reverts requires custom logic for each script,
    # as their effects are varied and not easily checked in a standardized way.
    # This part is intentionally left out as per the initial focus on structured data.
    if definition.script and definition.script.revert:
        # Placeholder for script revert tests.
        # For example, for 'powercfg.exe /hibernate on', one might check the output of 'powercfg /a'.
        # This requires specific command and output parsing for each case.
        pass
