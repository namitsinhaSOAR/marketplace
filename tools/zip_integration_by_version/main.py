# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import annotations

import argparse
import enum
import json
import logging
import pathlib
import subprocess
import zipfile
from typing import Any

MARKETPLACE_PATH: pathlib.Path = pathlib.Path(__file__).parent.parent.parent
CURRENT_INTEGRATIONS_PATH: pathlib.Path = (
    MARKETPLACE_PATH / "integrations" / "third_party"
)
PREVIOUS_INTEGRATIONS_PATH: pathlib.Path = MARKETPLACE_PATH / "Integrations"
INTEGRATION_DEF: str = "Integration-{0}.def"
RN_JSON: str = "RN.json"
PYTHON_UPDATE_MSG: str = (
    "Important - Updated the integration code to work with Python version 3.11."
    " To ensure compatibility and avoid disruptions, follow the upgrade best practices"
    " described in the following document:"
    " https://cloud.google.com/chronicle/docs/soar/respond/integrations-setup/"
    "upgrade-python-versions"
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class GitResetOption(enum.Enum):
    MIXED = "--mixed"
    SOFT = "--soft"
    HARD = "--hard"


def main() -> None:  # noqa: D103
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    args: argparse.Namespace = get_parsed_arguments(parser)
    validate_args(args)
    original_branch = get_current_branch()
    success = False
    try:
        commit_sha: str = get_commit_sha(
            integration=args.integration, version=args.version
        )
        logger.info("Commit SHA found %s", commit_sha)
        git_checkout(commit_sha)
        validate_integration(
            args.integration, args.version, args.raise_python_migration_rn
        )
        adjust_integration(args.integration)
        zip_integration(args.integration, args.version, args.dir)
        success = True
        logger.info(
            "Successfully created zip for %s version %s", args.integration, args.version
        )

    except Exception:
        logger.exception("Error during execution")

    finally:
        if success:
            try:
                restore_environment(original_branch)
            except Exception:
                logger.exception(
                    "Couldn't fully restore environment, but zip was created successfully"
                )
                logger.error(
                    "Note: Couldn't fully restore Git state, but zip was created successfully."
                )
        else:
            try:
                restore_environment(original_branch)
            except Exception:
                logger.exception(
                    "Error: Failed to restore Git state. You may need to run 'git checkout <your-branch>' manually."
                )


def get_parsed_arguments(parser: argparse.ArgumentParser) -> argparse.Namespace:
    parser.add_argument("-i", "--integration", help="Specify the integration's name.")
    parser.add_argument("-v", "--version", help="Specify the requested version to zip")
    parser.add_argument("-d", "--dir", help="The zip's dir. Default is repo base root")
    parser.add_argument(
        "--raise-python-migration-rn",
        help="Raise if python migration release note appear in the integration's RN",
        action="store_false",
    )
    return parser.parse_args()


def validate_args(arguments: argparse.Namespace) -> None:
    arguments.version = _validate_version(arguments.version)
    _validate_integration(arguments.integration)
    arguments.dir = _validate_dir(arguments.dir)


def _validate_version(version: float) -> float:
    try:
        return float(version)
    except ValueError as e:
        msg = (
            f"the value of -v/--version must be a number. Received {version}"
            f" of type {type(version)}"
        )
        raise ValueError(msg) from e


def _validate_integration(integration: str) -> None:
    integration_path: pathlib.Path = find_integration(integration)
    if not integration_path.exists():
        msg = f"the value of -i/--integration wasn't found in {integration_path}"
        raise ValueError(msg)


def _validate_dir(dir_: str) -> pathlib.Path:
    zip_dir: pathlib.Path = pathlib.Path(dir_) if dir_ else MARKETPLACE_PATH
    if not zip_dir.exists():
        msg = f"Could not find dir {zip_dir}"
        raise FileNotFoundError(msg)
    return zip_dir


def get_commit_sha(integration: str, version: float) -> str:
    def_name: str = INTEGRATION_DEF.format(integration)
    integration_def: pathlib.Path = find_integration(integration, def_name)
    try:
        cmd = f"git log -S '\"Version\": {version}' --all -p -- '{integration_def}'"
        logger.info(cmd)
        result = subprocess.run(  # noqa: S602
            cmd,
            cwd=MARKETPLACE_PATH,
            shell=True,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            log_output = result.stdout.strip()
            commit_lines = log_output.split("\n")
            last_commit = None
            for line in commit_lines:
                if line.startswith("commit "):
                    last_commit = line.split()[1]
            if last_commit:
                return last_commit
    except Exception:
        logger.exception(
            "Error searching in origin/develop branch, path %s", integration_def
        )
    msg = (
        f"No commit found for integration {integration} "
        f"at version {version} in branch origin/develop"
    )
    raise ValueError(msg)


def get_current_branch() -> str:
    """Get the name of the current Git branch."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=MARKETPLACE_PATH,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        print("Warning: Could not determine current branch")
        return ""


def git_checkout(commit_sha: str, quiet: bool = False) -> None:
    try:
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=MARKETPLACE_PATH,
            capture_output=True,
            text=True,
            check=True,
        )
        has_local_changes = bool(status_result.stdout.strip())
        if has_local_changes:
            print("Stashing local changes...")
            _run_command_safe("git stash")
        else:
            print("No local changes to save")
        subprocess.run(["git", "clean", "-fd"], cwd=MARKETPLACE_PATH, check=False)
        print(f"Fetching updates and checking out commit {commit_sha}...")
        _run_command_safe("git fetch --all")
        checkout_cmd = f"git checkout {commit_sha}{' -q' if quiet else ''}"
        try:
            _run_command_safe(checkout_cmd)
            return
        except subprocess.CalledProcessError:
            fetch_cmd = f"git fetch origin {commit_sha}"
            _run_command_safe(fetch_cmd)
            _run_command_safe(checkout_cmd)
            return
    except subprocess.CalledProcessError as e:
        print(f"Checkout failed: {e}")
        raise ValueError(f"Could not checkout commit {commit_sha}")


def adjust_integration(integration: str) -> None:
    def_name: str = INTEGRATION_DEF.format(integration)
    integration_def: pathlib.Path = find_integration(integration, def_name)
    def_: dict[str, Any] = json.loads(integration_def.read_text(encoding="utf-8"))
    def_["IsCustom"] = True
    integration_def.write_text(json.dumps(def_, indent=4), encoding="utf-8")


def validate_integration(
    integration: str,
    version: float,
    check_python_migration_rn: bool,
) -> None:
    _validate_integration_version_in_def(integration, version)
    if check_python_migration_rn:
        _validate_integration_python_migration_rn_description(integration)


def _validate_integration_version_in_def(integration: str, version: float) -> None:
    def_name: str = INTEGRATION_DEF.format(integration)
    integration_def: pathlib.Path = find_integration(integration, def_name)
    def_: dict[str, Any] = json.loads(integration_def.read_text(encoding="utf-8"))
    if def_["Version"] != version:
        raise RuntimeError(
            f"The integration's version doesn't match the requested version."
            f" Expected {version!r}, got {def_['Version']}"
        )


def _validate_integration_python_migration_rn_description(integration: str) -> None:
    rn_path: pathlib.Path = find_integration(integration, RN_JSON)
    rns: list[dict[str, Any]] = json.loads(rn_path.read_text(encoding="utf-8"))
    changes: set[str] = {rn["ChangeDescription"] for rn in rns}
    if not changes:
        raise RuntimeError("No RNs found")


def zip_integration(integration: str, version: float, dir_: pathlib.Path) -> None:
    integration_path: pathlib.Path = find_integration(integration)
    version_s: str = str(version).replace(".", "-")
    zip_path: pathlib.Path = dir_ / f"{integration}_V{version_s}.zip"
    with zipfile.ZipFile(zip_path, "w") as integration_zip:
        for file in integration_path.rglob("*"):
            if file.is_file():  # Only add files, not directories
                integration_zip.write(file, arcname=file.relative_to(integration_path))
    print(f"Created zip file: {zip_path}")


def find_integration(integration: str, filename: str = None) -> pathlib.Path:
    if filename:
        integration_path = CURRENT_INTEGRATIONS_PATH / integration / filename
        if not integration_path.exists():
            integration_path = PREVIOUS_INTEGRATIONS_PATH / integration / filename
    else:
        integration_path = CURRENT_INTEGRATIONS_PATH / integration
        if not integration_path.exists():
            integration_path = PREVIOUS_INTEGRATIONS_PATH / integration
    return integration_path


def restore_environment(original_branch: str) -> None:
    print("Restoring Git environment...")
    _run_command_safe("git restore .")
    if original_branch:
        try:
            checkout_cmd = f"git checkout {original_branch}"
            result = _run_command_safe(checkout_cmd)
            if result and result.returncode == 0:
                print(f"Successfully restored to branch: {original_branch}")
            else:
                print(
                    f"Warning: Could not restore to original branch '{original_branch}'"
                )
        except Exception as e:
            print(f"Warning: Failed to restore original branch: {e}")
    try:
        stash_list = subprocess.run(
            ["git", "stash", "list"],
            cwd=MARKETPLACE_PATH,
            capture_output=True,
            text=True,
            check=True,
        )
        if stash_list.stdout.strip():
            _run_command_safe("git stash pop")
            print("Restored stashed changes")
        else:
            print("No stashed changes to restore")
    except Exception as e:
        print(f"Warning: Failed to restore stashed changes: {e}")


def _run_command_safe(command: str | list[str]) -> None:
    if isinstance(command, str):
        command = command.split()
    try:
        result = subprocess.run(
            command,
            cwd=MARKETPLACE_PATH.absolute(),
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            print(
                f"Warning: Command {' '.join(command)} failed with code {result.returncode}: {result.stderr}"
            )
        return result
    except Exception as e:
        print(f"Warning: Failed to run command {' '.join(command)}: {e}")
        return None


if __name__ == "__main__":
    main()
