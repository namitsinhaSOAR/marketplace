#!/bin/sh

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

# shellcheck disable=SC3030
# shellcheck disable=SC3043

VERBOSE=false
QUIET=false
INTEGRATIONS=()

main() {
  init_args "${@}"
  test_integrations
  local final_status=$?
  if [ ${final_status} -eq 0 ]; then
    print_with_color "[INFO] All operations completed successfully."
  else
    print_with_color "[INFO] Operations failed. Final status: ${final_status}"
  fi
  exit ${final_status}
}

test_integrations() {
  # shellcheck disable=SC3054
  for integration in "${INTEGRATIONS[@]}"; do
    log_debug "#### Processing integration: ${integration} ####"
    test_integration "${integration}"
    local integration_status=$?
    if [ ${integration_status} -ne 0 ]; then
      log_error "Processing failed for integration '${integration}' with status ${integration_status}."
      return ${integration_status} # Exit test_integrations with the error code
    fi
    log_debug "Integration '${integration}' processed successfully."
  done
  log_debug "All integrations processed successfully."
  return 0 # All integrations passed
}

test_integration() {
  integration_path="$1"
  validate_directory "${integration_path}" # Exits script on error

  integration_tests_path="${integration_path}/tests"
  if [ -d "${integration_tests_path}" ]; then
    log_debug "Integration tests path: ${integration_tests_path}"

    local original_dir
    original_dir=$(pwd)
    if ! cd "${integration_path}"; then
      log_error "Failed to cd to ${integration_path}"
      return 1 # Return error status
    fi

    # After cd, venv_path is relative to the integration directory
    local venv_path=".venv"

    log_debug "Syncing venv in $(pwd)/${venv_path}"
    sync_venv "${venv_path}"
    local sync_status=$?
    if [ ${sync_status} -ne 0 ]; then
      log_error "Failed to sync venv for ${integration_path}. Status: ${sync_status}"
      # Attempt to cd back before returning
      if ! cd "${original_dir}"; then
        log_error "Critical: Failed to cd back to ${original_dir}."
        exit 1
      fi
      return ${sync_status}
    fi

    log_debug "Sourcing venv $(pwd)/${venv_path}/bin/activate"
    source_venv "${venv_path}"
    local source_status=$?
    if [ ${source_status} -ne 0 ]; then
      log_error "Failed to source venv for ${integration_path}. Status: ${source_status}"
      if ! cd "${original_dir}"; then
        log_error "Critical: Failed to cd back to ${original_dir}."
        exit 1
      fi
      return ${source_status}
    fi

    log_debug "Running tests for integration ${integration_path}"
    run_tests "${venv_path}" # venv_path is relative, e.g., ".venv"
    local test_status=$?
    log_debug "Tests for ${integration_path} finished with status ${test_status}."

    if type deactivate >/dev/null 2>&1; then
      log_debug "Deactivating venv"
      deactivate
    fi

    if ! cd "${original_dir}"; then
      log_error "Critical: Failed to cd back to ${original_dir} from $(pwd). Exiting."
      exit 1 # This is a critical failure affecting script integrity
    fi

    return ${test_status}
  else
    log_debug "No tests directory found at ${integration_tests_path}. Skipping tests for ${integration_path}."
    return 0 # No tests to run, so success for this integration's test phase.
  fi
}

validate_directory() {
  path="$1"
  if [ ! -d "${path}" ]; then
    log_error "${path} does not exist"
    exit 1
  fi
}

sync_venv() {
  venv_path="$1"
  # This function assumes it's called from within the integration's directory
  if [ -d "${venv_path}" ]; then
    log_debug "Virtual environment already exists in $(pwd)/${venv_path}"
  else
    log_debug "Creating new virtual environment in $(pwd)/${venv_path}"
    local sync_cmd_output
    local sync_status
    if [ "${VERBOSE}" = true ]; then
      sync_cmd_output=$(uv sync --dev --verbose 2>&1)
      sync_status=$?
    elif [ "${QUIET}" = true ]; then
      sync_cmd_output=$(uv sync --dev --quiet 2>&1)
      sync_status=$?
    else
      sync_cmd_output=$(uv sync --dev 2>&1)
      sync_status=$?
    fi

    if [ ${sync_status} -ne 0 ]; then
      log_error "uv sync failed with status ${sync_status} for $(pwd)/${venv_path}"
      if [ -n "${sync_cmd_output}" ]; then log_error "uv sync output: ${sync_cmd_output}"; fi
      return ${sync_status} # Propagate error
    else
      if [ "${VERBOSE}" = true ] && [ -n "${sync_cmd_output}" ]; then log_debug "uv sync output: ${sync_cmd_output}"; fi
    fi
  fi
  return 0 # Success
}

source_venv() {
  local venv_path="$1" # e.g., ".venv" when called from within integration dir
  local venv_activate_script="${venv_path}/bin/activate"
  log_debug "Attempting to source venv: $(pwd)/${venv_activate_script}"
  if [ -f "${venv_activate_script}" ]; then
    # shellcheck disable=SC1090
    . "${venv_activate_script}"
    return 0 # Success
  else
    log_error "Activation script not found: $(pwd)/${venv_activate_script}"
    return 1 # Return 1 if activation script is not found
  fi
}

run_tests() {
  venv_path="$1" # e.g., ".venv"
  # Assumes CWD is the integration directory, so ./tests is correct
  if [ "${VERBOSE}" = true ]; then
    "${venv_path}/bin/python3" -m pytest -vv ./tests
  elif [ "${QUIET}" = true ]; then
    "${venv_path}/bin/python3" -m pytest -qq ./tests
  else
    "${venv_path}/bin/python3" -m pytest ./tests
  fi
  # The exit status of pytest will be the implicit return status of this function
}

print_with_color() {
  printf "%b\n" "$1"
}

log_error() {
  # Consider printing errors to stderr: >&2
  print_with_color "[ERROR] $1" >&2
}

log_debug() {
  if [ "${VERBOSE}" = true ]; then
    print_with_color "[DEBUG] $1"
  fi
}

init_args() {
  while [ ${#} -gt 0 ]; do
    case "$1" in
    -v | --verbose)
      VERBOSE=true
      shift
      ;;
    -q | --quiet)
      QUIET=true
      shift
      ;;
    *)
      # shellcheck disable=SC3024
      INTEGRATIONS+=("$1")
      shift
      ;;
    esac
  done
}

main "${@}"
