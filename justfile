_:
  @just --list --unsorted

json:
  uv run src/winconfig/scripts/generate_definitions.py
  bunx prettier --write src/winconfig/definitions/*_definitions.yaml

jsonschema:
  uv run src/winconfig/scripts/generate_schema.py
  bunx prettier --write src/winconfig/definitions/schema.json
