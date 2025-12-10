set unstable

_:
  @just --list --unsorted

additional_definition := "samples/winconfig.additional.definition.yaml"
taskplan := "samples/winconfig.plan.yaml"
winconfig_schema := "samples/winconfig.plan.schema.json"
builtin_definition_schema := "src/winconfig/resources/builtin.definition.schema.json"

apply:
  uv run src/winconfig/cli/main.py apply {{taskplan}} -e {{additional_definition}}

test:
  powershell.exe -ExecutionPolicy Bypass -File tests/run_test_in_wsb.ps1 -Headless false

build:
  uv run pyinstaller \
    --onefile src/winconfig/cli/main.py \
    --add-data "src/winconfig/resources:winconfig/resources" \
    -n winconfig --workpath dist --uac-admin --noconfirm
  # uv run nuitka --mode=onefile src/winconfig/cli/main.py --output-filename=winconfig --mingw64 --output-dir=dist --windows-uac-admin --assume-yes-for-downloads

schema:
  uv run src/winconfig/cli/main.py schema taskplan --output {{winconfig_schema}} -e {{additional_definition}}
  bunx prettier --write {{winconfig_schema}}
  uv run src/winconfig/cli/main.py schema definition --output {{builtin_definition_schema}}
  bunx prettier --write {{builtin_definition_schema}}

memo:
  robocopy C:\winconfig-readonly C:\winconfig /s /xf .* /xd .*
  cd C:\winconfig
  uv run pytest --durations 0 tests/test_apply.py -v
