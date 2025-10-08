import subprocess
from pathlib import Path

import pytest
import yaml

from winconfig.model.definition import Definition, DefinitionContainer

DEFINITIONS_FILE = Path("src/winconfig/definitions/winutil_definitions.yaml")
definitions = DefinitionContainer.model_validate(
    yaml.safe_load(DEFINITIONS_FILE.read_text())
).root


@pytest.mark.parametrize("definition", definitions, ids=[d.name for d in definitions])
def test_default_scheduled_task(definition: Definition):
    """
    Tests the revert values for each definition by checking the current system state.
    """

    for task in definition.scheduled_tasks:
        result = subprocess.run(
            ["schtasks", "/query", "/tn", task.path, "/fo", "list"],
            capture_output=True,
            text=True,
            check=True,
        )

        current_state = ""
        for line in result.stdout.splitlines():
            if line.startswith("Status:"):
                status = line.split(":")[1].strip()
                if status == "Ready":
                    current_state = "Enabled"
                elif status == "Disabled":
                    current_state = "Disabled"
                break
        assert current_state == task.old_state, (
            f"[{definition.name}] Scheduled Task '{task.path}' expected state '{task.old_state}', but got '{current_state}'."
        )
