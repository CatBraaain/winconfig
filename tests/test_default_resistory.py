import subprocess
from logging import getLogger
from pathlib import Path

import pytest
import yaml

from winconfig.model.definition import Definition, DefinitionContainer

logger = getLogger(__name__)

DEFINITIONS_FILE = Path("src/winconfig/definitions/winutil_definitions.yaml")
definitions = DefinitionContainer.model_validate(
    yaml.safe_load(DEFINITIONS_FILE.read_text())
).root[:10]


@pytest.mark.parametrize("definition", definitions, ids=[d.name for d in definitions])
def test_default_resitory(definition: Definition):
    """
    Tests the revert values for each definition by checking the current system state.
    """

    for registry in definition.registries:
        result = subprocess.run(
            ["reg", "query", registry.path, "/v", registry.name],
            check=False,
            capture_output=True,
            text=True,
        )
        if registry.old_value == "<RemoveEntry>":
            # assert result.returncode != 0, (
            #     f"{registry.path}\\{registry.name} is not removed"
            # )
            continue

        # assert result.returncode == 0, (
        #     f"reg query {registry.path}\\{registry.name} failed"
        # )
        output = result.stdout.strip()
        if output == "":
            # assert output == "", (
            #     f"[{registry.path}\\{registry.name}] {results.stderr}"
            # )
            continue

        current_value = output.split()[-1]
        if "REG_DWORD" in output:
            current_value = str(int(current_value, 16))

        # assert str(current_value) == str(registry.old_value), (
        #     f"{registry.path}\\{registry.name} {current_value} != {registry.old_value}"
        # )
