_:
  @just --list --unsorted

jsonschema:
  uv run src/winconfig/scripts/generate_schema.py
  bunx prettier --write config_tasks/schema.json
