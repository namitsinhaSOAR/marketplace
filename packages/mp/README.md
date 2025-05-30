# mp: Your Google SecOps Marketplace Integration Powerhouse

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
![Maintenance](https://img.shields.io/maintenance/yes/2025)

**`mp`**, short for **`google_secops_marketplace`**, is a command-line interface (CLI) tool designed to streamline the development and maintenance of Google SecOps marketplace integrations. It empowers developers by providing a unified platform for building, testing, and ensuring the quality of their integrations.

## Key Features

- **Build Integrations**: Convert non-built integrations to the format required by Google SecOps Marketplace
- **Deconstruct Integrations**: Convert built integrations back to source code format
- **Code Quality**: Format and lint Python code with ruff, and statically type-check with mypy
- **Developer Workflow**: Streamline the development process with helpful commands and fast dependency management using uv

## Documentation

For detailed information on how to use and contribute to `mp`, please refer to the documentation:

- [Installation Guide](docs/installation.md) - How to install the tool
- [Usage Guide](docs/usage.md) - How to use the available commands
- [Development Guide](docs/development.md) - How to set up your development environment
- [Marketplace Integration Guide](docs/marketplace.md) - How to work with marketplace integrations
- [Contributing Guidelines](docs/CONTRIBUTING.md) - How to contribute to the project

## Quick Start

```bash
# Install the package
uv pip install .

# Get help
mp --help

# Format Python files
mp format path/to/files

# Check code quality
mp check path/to/files --static-type-check --lint

# Build an integration
mp build --integration my_integration
```

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

* **Effortless Integration Building:** Simplify the creation of new Google SecOps integrations with intuitive commands and project scaffolding.
* **Automated Code Checks:** Ensure code quality and adherence to best practices through integrated code analysis.
* **Linting and Formatting:** Automatically identify and fix stylistic issues, maintaining a consistent and readable codebase.
* **Testing Capabilities:** Run unit tests and initiate black box tests to validate the functionality and reliability of your integrations.

## Getting Started

### Installation

```bash
uv pip install google_secops_marketplace