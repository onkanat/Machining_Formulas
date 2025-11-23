# Machining Formulas - Agent Guidelines

## Build/Test Commands
- **Run all tests**: `PYTHONPATH=. pytest tests/`
- **Run single test**: `PYTHONPATH=. pytest tests/test_file.py::test_function_name`
- **Run with verbose output**: `PYTHONPATH=. pytest -v tests/`
- **V3 Complete tests**: `python3 test_v3_complete.py`
- **V3 Enhanced tests**: `python3 test_v3_enhanced.py`
- **Install dependencies**: `pip install -r requirements.txt`
- **Launch V3 GUI**: `python3 v3_gui_direct.py`

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
- V3 GUI: `v3_gui_direct.py` (production version)
- Workspace: `workspace_buffer.py` for collaborative editing
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

## Project Status
- **Current Version**: V3 (Production Ready)
- **Main GUI**: `v3_gui_direct.py`
- **All Tests Passing**: 9/9 tests complete
- **Repository**: Clean and synchronized
- **Last Updated**: V3 official release with all enhancements

## Key Files
- Core logic: `engineering_calculator.py`
- GUI/LLM: `horz_gui.py`
- V3 GUI: `v3_gui_direct.py` (production)
- Workspace: `workspace_buffer.py` (collaborative editing)
- Tool schemas: `ollama_utils.py` / `ollama_utils_v2.py`
- Parameter handling: `material_utils.py`
- Tests: `tests/` directory
- UI labels: `tooltips.json`

## V3 GUI Features
- **Keyboard Shortcuts**: Ctrl+S/O/N/M, Ctrl+1/2/3/4, F1 (help)
- **Accessibility**: High contrast mode, larger fonts, full keyboard navigation
- **Performance**: Debounced calculations, loading indicators, <1s operations
- **Workspace**: Collaborative editing with version history and AI suggestions
- **Testing**: Complete test suite with 9/9 tests passing