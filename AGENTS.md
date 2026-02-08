# Machining Formulas - Agent Guidelines

## Build/Test Commands
- **Install dependencies**: `pip install -r requirements.txt`
- **Install project (src/ layout)**: `pip install -e .`
- **Launch V3 GUI (entrypoint)**: `python -m machining_formulas`
- **Run all tests**: `pytest tests/`
- **Run all tests (safe fallback)**: `PYTHONPATH=. pytest tests/`
- **Run single test**: `pytest tests/test_file.py::test_function_name`
- **Run with verbose output**: `pytest -v tests/`
- **V3 complete tests (legacy scripts)**: `python test_v3_complete.py`
- **V3 enhanced tests (legacy scripts)**: `python test_v3_enhanced.py`

> Not: Repo `src/` layout kullanır. Bu yüzden `python -m machining_formulas` komutu için
> proje paketinin kurulu olması gerekir (`pip install -e .`) veya `PYTHONPATH=src` verilmelidir.

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
- V3 GUI: `src/machining_formulas/gui/v3_gui.py` (entrypoint: `python -m machining_formulas`)
- Workspace: `src/machining_formulas/workspace/*` for collaborative editing
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
- **Current Version**: V3
- **Main GUI entrypoint**: `python -m machining_formulas`
- **Repository layout**: `src/machining_formulas/*` (package), `assets/*` (static files)
- **Validation**: `pytest tests/` (hidden tests may exist)

## Key Files
- Core logic: `src/machining_formulas/core/engineering_calculator.py`
- V3 GUI: `src/machining_formulas/gui/v3_gui.py`
- Tool-calling (tests focus): `src/machining_formulas/gui/advanced_calculator.py`
- Execute mode (eval safety): `src/machining_formulas/gui/execute_mode.py`
- Workspace: `src/machining_formulas/workspace/workspace_buffer.py`, `workspace_editor.py`, `workspace_manager.py`
- Tool schemas + URL helpers: `src/machining_formulas/llm/ollama_utils.py`
- V3 GUI Ollama helpers: `src/machining_formulas/llm/ollama_utils_v2.py`
- Parameter handling: `src/machining_formulas/llm/material_utils.py`
- Assets path helper: `src/machining_formulas/assets.py`
- UI labels: `assets/tooltips.json`
- Tests: `tests/` directory

### Legacy note

Bu doküman, kanonik `src/` paket yapısını temel alır. Kök dizinde bulunabilecek eski dosyalar
(örn. `horz_gui.py`, `v3_gui_direct.py`) varsa bile yeni geliştirmeler için referans alınmamalıdır.

## V3 GUI Features
- **Keyboard Shortcuts**: Ctrl+S/O/N/M, Ctrl+1/2/3/4, F1 (help)
- **Accessibility**: High contrast mode, larger fonts, full keyboard navigation
- **Performance**: Debounced calculations, loading indicators, <1s operations
- **Workspace**: Collaborative editing with version history and AI suggestions
- **Testing**: Complete test suite with 9/9 tests passing