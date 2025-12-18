set unstable

_:
  @just --list --unsorted

config := "samples/winconfig.config.yaml"
config_schema := "samples/winconfig.config.schema.json"
builtin_definition_schema := "src/winconfig/resources/builtin.definition.schema.json"

run:
  uv run src/winconfig/cli/main.py run {{config}}

test:
  powershell.exe -ExecutionPolicy Bypass -File tests/run_test_in_wsb.ps1 -Headless false

pyinstaller:
  uv run pyinstaller \
    --onefile src/winconfig/cli/main.py \
    --add-data "src/winconfig/resources:winconfig/resources" \
    -n winconfig --workpath dist --uac-admin --noconfirm

nuitka:
  uv run nuitka --mode=onefile src/winconfig/cli/main.py --output-filename=winconfig --mingw64 --output-dir=dist --windows-uac-admin --assume-yes-for-downloads

schema:
  uv run src/winconfig/cli/main.py schema {{config}} --output {{config_schema}} --strict
  bunx prettier --write {{config_schema}}
  uv run src/winconfig/cli/main.py schema --output {{builtin_definition_schema}}
  bunx prettier --write {{builtin_definition_schema}}

refresh-wsb:
  robocopy C:\winconfig-readonly C:\winconfig /s /xf .* /xd .*
  cd C:\winconfig
  uv run pytest --durations 0 tests/test_builtin_definition.py -v
