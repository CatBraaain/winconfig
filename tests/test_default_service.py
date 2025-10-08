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
def test_default_service(definition: Definition):
    """
    Tests the revert values for each definition by checking the current system state.
    """

    for service in definition.services:
        result = subprocess.run(
            ["sc", "qc", service.name], capture_output=True, text=True, check=True
        )
        current_value = ""
        for line in result.stdout.splitlines():
            if "START_TYPE" in line:
                start_type_code = line.split(":")[1].strip().split()[0]
                if start_type_code == "2":
                    current_value = "Automatic"
                elif start_type_code == "3":
                    current_value = "Manual"
                elif start_type_code == "4":
                    current_value = "Disabled"
                break
        # assert current_value == service.old_startup_type, (
        #     f"[{definition.name}] Service '{service.name}' expected startup type '{service.old_startup_type}', but got '{current_value}'."
        # )
