set unstable

_:
  @just --list --unsorted

json:
  uv run scripts/generate_schema.py
  uv run scripts/generate_definitions.py

apply:
  uv run src/winconfig/cli/main.py apply --path winconfig.config.yaml

test:
  powershell.exe -ExecutionPolicy Bypass -File tests/run_wsb.ps1 -Headless false
