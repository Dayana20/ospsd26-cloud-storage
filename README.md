# Python Application Template: A Component-Based Cloud Storage API

[![CircleCI](https://circleci.com/gh/Dayana20/ospsd26-cloud-storage.svg?style=shield)](https://circleci.com/gh/Dayana20/ospsd26-cloud-storage)
[![Coverage](https://img.shields.io/badge/coverage-85%2B%25-brightgreen)](https://circleci.com/gh/Dayana20/ospsd26-cloud-storage)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://python.org)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

This repository defines a shared, provider-independent contract for document
storage. It demonstrates a component-based architecture by defining the common
operations, file metadata, and errors that storage-provider implementations
can share.

The project emphasizes a strict separation of concerns and a comprehensive,
automated toolchain to enforce code quality and best practices. This repository
contains the storage contract; concrete provider implementations can be
developed as separate components.

## Architectural Philosophy

This project is built on the principle of "programming integrated over time."
The architecture is designed to combat complexity and ensure the system is
maintainable and evolvable.

- **Component-Based Design:** Components have a single responsibility and can
  be reused in other projects with minimal coupling.
- **Interface-Implementation Separation:** Functionality is defined by an
  abstract contract (the "what") and fulfilled by a concrete implementation
  (the "how"). This decouples storage consumers from provider-specific
  details.
- **Dependency Injection:** Applications depend on the stable storage
  interface and receive a provider implementation separately.

## Core Components

The project is a `uv` workspace containing the shared contract package:

- **`cloud_storage_api`**: Defines the abstract `DocumentStorage` interface,
  the `FileInfo` metadata model, and shared storage errors.
- **Storage provider implementations**: Not included in this repository.
  Provider adapters can be developed as separate packages implementing the
  shared contract.

## Project Structure

```
ospsd26-cloud-storage/
├── src/                          # Source packages (uv workspace members)
│   └── cloud_storage_api/        # Shared document-storage contract
│       ├── src/cloud_storage_api/
│       └── tests/
├── tests/                        # Additional project-level tests, when needed
├── docs/                         # Documentation source files
├── .circleci/                    # CircleCI configuration
├── main.py                       # Read-only contract usage example
├── pyproject.toml                # Project configuration (dependencies, tools)
└── uv.lock                       # Locked dependency versions
```

## Project Setup

### 1. Prerequisites

- Python 3.12 or higher
- `uv` – a Python package manager and project tool.

### 2. Initial Setup

1. **Install `uv`:**
   ```bash
   # macOS / Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # Windows (PowerShell)
   irm https://astral.sh/uv/install.ps1 | iex
   ```

2. **Clone the repository:**
   ```bash
   git clone <your-repository-url>
   cd ospsd26-cloud-storage
   ```

3. **Create and sync the virtual environment:**

   Create the project-local `.venv` with the supported Python version, then
   install all workspace packages and development tools defined in `uv.lock`.

   ```bash
   uv venv --python 3.12
   uv sync --all-packages --extra dev
   ```

5.  **Activate the Virtual Environment:**
    ```bash
    # macOS / Linux
    source .venv/bin/activate
    # Windows (PowerShell)
    .venv\Scripts\Activate.ps1
    ```

6.  **Perform Initial Authentication:**
    Run the main application once to perform the interactive OAuth flow. This will open a browser window for you to grant permission.
    ```bash
    uv run python main.py
    ```
    After you approve, a `token.json` file will be created. This file is also ignored by `.gitignore` and will be used for authentication in subsequent runs.

## Development Workflow

All commands should be run from the project root with the virtual environment activated.

### Running the Application

To run the main demonstration script:
```bash
uv run python main.py
```

### Running the Toolchain

-   **Linting & Formatting (Ruff):**
    The project uses Ruff with comprehensive rules configured in `pyproject.toml`.
    ```bash
    # Check for issues
    uv run ruff check .
    # Automatically fix issues
    uv run ruff check . --fix
    # Check formatting
    uv run ruff format --check .
    # Apply formatting
    uv run ruff format .
    ```

-   **Static Type Checking (MyPy):**
    ```bash
    uv run mypy src tests
    ```

-   **Testing (Pytest):**

  The shared contract tests are fast and do not require external services.
  ```bash
  # Run the cloud storage contract tests
  uv run pytest src/cloud_storage_api/tests -q

  # Run all discovered tests
  uv run pytest

    # Run tests with coverage reporting
    uv run pytest --cov=src --cov-report=term-missing
    ```

### Viewing Documentation

This project uses MkDocs for documentation.
```bash
# Start the live-reloading documentation server
uv run mkdocs serve
```
Open your browser to `http://127.0.0.1:8000` to view the site.

## Testing Infrastructure

The project implements a sophisticated testing strategy designed for both local development and CI/CD environments:

### Test Categories

- **Unit Tests** (`src/*/tests/`): Fast, isolated tests with mocked dependencies
- **Integration Tests** (`tests/integration/`): Tests that verify component interactions
- **End-to-End Tests** (`tests/e2e/`): Full application workflow tests
- **CircleCI Tests**: CI/CD-compatible tests that handle missing credentials gracefully
- **Local Credentials Tests**: Tests that require `credentials.json` or `token.json` files

### Test Markers

The project defines pytest markers for organizing tests:

```python
@pytest.mark.unit
@pytest.mark.integration
@pytest.mark.e2e
@pytest.mark.circleci
@pytest.mark.local_credentials
```

Provider integration tests should use the `integration` marker. Provider
credentials should be supplied through the provider's CI secret context, not
stored in the repository.

## Continuous Integration

The project includes a comprehensive CircleCI configuration (`.circleci/config.yml`) with:

- **All Branches**: Unit tests, linting, and CI-compatible tests
- **Main/Develop**: Additional integration tests with real Gmail API calls
- **Artifacts**: Coverage reports, test results, and build summaries

See `docs/circleci-setup.md` for detailed CI/CD setup instructions.

## Development Workflow

### Quick Start
1. **Install dependencies**: `uv sync --all-packages --extra dev`
2. **Run tests**: `uv run pytest tests/ -v` or `uv run pytest src/ tests/ -m "not local_credentials" -v`
3. **Check code quality**: `uv run ruff check . && uv run ruff format --check .`
4. **Fix formatting**: `uv run ruff format .`
5. **View documentation**: `uv run mkdocs serve`

### Best Practices
- Run unit tests (`uv run pytest src/`) during development for fast feedback
- Use integration tests (`uv run pytest -m integration`) to verify component interactions
- Run full test suite (`uv run pytest`) before pushing to ensure CI compatibility
- The CircleCI pipeline provides automated validation on every push