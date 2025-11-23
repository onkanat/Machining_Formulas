# Machining Formulas - Agent Guidelines

## Build/Test Commands
- **Run all tests**: `pytest tests/`
- **Run single test**: `pytest tests/test_file.py::test_function_name`
- **Run with verbose output**: `pytest -v tests/`
- **Install dependencies**: `pip install -r requirements.txt`

## Code Style Guidelines

### Imports & Formatting
- Use autopep8 formatter (configured in .vscode/settings.json)
- Python 3.10+ type hints required
- Import order: standard library → third-party → local imports
- Use `from __future__ import annotations` for dataclasses

### Naming Conventions
- Functions/variables: `snake_case` (English)
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Turkish UI strings only in user-facing messages

### Error Handling
- Wrap errors in `ValueError` with descriptive messages
- Use Turkish error messages for users, English for developers
- Include context in error messages

### Architecture Patterns
- Core calculations in `EngineeringCalculator` class
- GUI/LLM layer in `AdvancedCalculator` class
- Tool definitions generated dynamically from calculator methods
- Parameter metadata via `get_calculation_params()` and `get_shape_parameters()`

### Unit Consistency
- Length: mm (internal), convert for display as needed
- Volume: mm³ (internal), cm³ for external mass calculations
- Speed: m/min, rpm
- MRR: cm³/min

### Testing Requirements
- Test all formula changes with known values
- Include edge cases: zero values, missing params, type errors
- Use `pytest.approx()` for float comparisons
- Mock external dependencies (Ollama API, GUI components)

### LLM Integration
- Tool names: `calculate_turning_{method}`, `calculate_milling_{method}`, `calculate_material_mass`
- Arguments must match calculator parameter definitions exactly
- Handle both `/v1/chat` and `/api/chat` Ollama endpoints
- Timeout: 20s for HTTP requests

### Security
- No API keys or secrets in code
- `ExecuteModeMixin` capsulates eval functionality
- Validate all user inputs before calculations

## Key Files
- Core logic: `engineering_calculator.py`
- GUI/LLM: `horz_gui.py`
- Tool schemas: `ollama_utils.py`
- Parameter handling: `material_utils.py`
- Tests: `tests/` directory
- UI labels: `tooltips.json`