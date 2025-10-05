_:
  @just --list --unsorted

json:
  uv run src/winconfig/scripts/generate_schema.py
  uv run src/winconfig/scripts/generate_definitions.py
