# Integration Zipper

This script automates the process of zipping a specific version of a Chronicle SOAR
integration. It retrieves the integration code from a given commit SHA, modifies the
integration definition file, and creates a zip file containing the integration's
contents.

## Prerequisites

- Python 3.11
- Git

## Usage

```shell
python zip_integration.py -i <integration_name> -v <version> [-d <zip_directory>] [--raise-python-migration-rn]
```

Example:

```shell
python Common/Scripts/zip_integration_by_version/main.py -i Exchange -v 55.0 -d ~/repos --raise-python-migration-rn
```
