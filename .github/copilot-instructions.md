# Copilot Instructions

## Project Guidelines
- In op-to-entity validation, an operation must be associated to the parent entity; sub-entity-only association should be treated as not associated.

## Code Style
- For table styling in `ops_grid.py`, apply style mapping only to tool columns, and exclude fixed columns: Operation, Paths Open, Recipe, CC Used, and PROCESS_NODE.