# CLAUDE.md

## Build & Run Commands
- Install dependencies: `poetry install`
- Run application: `poetry run python app.py`
- Run all tests: `poetry run pytest`
- Run single test: `poetry run pytest tests/path/to/test_file.py::test_function`
- Lint code: `poetry run ruff check .`
- Type check: `poetry run mypy .`

## Code Style Guidelines
- **Formatting**: Use Black with 88 character line length
- **Imports**: Group standard library, third-party, and local imports with blank lines between
- **Types**: Use type hints for all function signatures; use Optional for nullable types
- **Naming**: snake_case for variables/functions, PascalCase for classes, UPPER_CASE for constants
- **Error Handling**: Use specific exceptions; prefer context managers; log exceptions appropriately
- **Documentation**: Document all public functions/classes with docstrings (Google style)
- **Testing**: Unit tests should cover core functionality; use pytest fixtures for test setup