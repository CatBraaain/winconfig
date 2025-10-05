_:
  @just --list --unsorted

json:
  uv run src/winconfig/scripts/generate_tasks.py
  bunx prettier --write src/winconfig/config_tasks/*_tasks.yaml

jsonschema:
  uv run src/winconfig/scripts/generate_schema.py
  bunx prettier --write src/winconfig/config_tasks/schema.json
