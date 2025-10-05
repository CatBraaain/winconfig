_:
  @just --list --unsorted

json:
  uv run scripts/generate_schema.py
  uv run scripts/generate_definitions.py
