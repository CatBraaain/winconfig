set unstable

_:
  @just --list --unsorted

apply:
  uv run src/winconfig/cli/main.py apply --path winconfig.config.yaml

test:
  powershell.exe -ExecutionPolicy Bypass -File tests/run_test_in_wsb.ps1 -Headless false

build:
  uv run pyinstaller \
    --onefile src/winconfig/cli/main.py \
    --add-data "src/winconfig/resources:winconfig/resources" \
    -n winconfig --workpath dist --uac-admin --noconfirm
  # uv run nuitka --mode=onefile src/winconfig/cli/main.py --output-filename=winconfig --mingw64 --output-dir=dist --windows-uac-admin --assume-yes-for-downloads

winconfig_schema_dist := "winconfig.plan.schema.json"
definition_schema_dist := "src/winconfig/resources/builtin.definition.schema.json"
schema:
  uv run src/winconfig/cli/main.py schema taskplan --output {{winconfig_schema_dist}}
  bunx prettier --write "{{winconfig_schema_dist}}"
  uv run src/winconfig/cli/main.py schema definition --output {{definition_schema_dist}}
  bunx prettier --write {{definition_schema_dist}}

memo:
  robocopy C:\winconfig-readonly C:\winconfig /s /xf .* /xd .*
  cd C:\winconfig
  uv run pytest --durations 0 tests/test_apply.py -v
