# Installation Guide

## Prerequisites

- Python 3.11 or later (Python 3.11.0+ is officially supported)
- uv package manager

## Installation Steps

### 1. Install `uv`

Install uv in your base Python interpreter:

```bash
pip install uv
```

### 2. Clone the Repository

```bash
git clone <repository-url>
cd mp
```

### 3. Set Up Project with `uv`

#### Development Installation

For development purposes, create a virtual environment and install dependencies in one
step:

```bash
uv sync --dev
```

This command creates a virtual environment in `.venv` directory and installs all
dependencies including development ones.

#### User Installation

For regular usage without development dependencies:

```bash
uv sync
```

### 4. Activate the Virtual Environment

```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 5. Verify Installation

Verify that the installation was successful by running:

```bash
mp --help
```

You should see the help menu displaying the available commands.

### Alternative: Direct Installation

You can also install the package directly to your base Python interpreter:

```bash
uv pip install .
# Or for development installation
uv pip install -e .
```

## Configure `mp`

When installing `mp` it automatically assumes the marketplace repo is installed at
`~/marketpalce`.
To configure a different path run

```shell
mp config --marketpalce-path /path/to/marketpalce 
```

To find more about configurations, run

```shell
mp config --help
```

## Dependencies

The tool automatically installs the following dependencies:

- libcst: For code structure transformations
- mypy: For static type checking (used as a core tool for the project)
- pyyaml: For YAML file handling
- rich: For enhanced terminal output
- ruff: For code linting and formatting (used as a core tool for the project)
- toml: For TOML file handling
- typer: For command-line interface
- uv: For fast and reliable package management (used as a core tool for the project)

## Development Dependencies

Development dependencies are automatically installed when using `uv sync --dev`.
These include:

- pytest: For running tests
- pytest-cov: For code coverage
- pytest-xdist: For parallel test execution
- type stubs for YAML and TOML

If you need to update dependencies after changes to pyproject.toml:

```bash
uv sync --dev
```
