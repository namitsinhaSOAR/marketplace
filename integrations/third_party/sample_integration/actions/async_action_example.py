import json
from typing import Iterable, List, NoReturn

from TIPCommon.base.action.data_models import ExecutionState
from TIPCommon.extraction import extract_action_param
from TIPCommon.rest.soar_api import get_case_overview_details
from TIPCommon.smp_time import is_approaching_action_timeout
from TIPCommon.validation import ParameterValidator
from soar_sdk.SiemplifyUtils import unix_now

from ..core.base_action import BaseAction
from ..core.constants import ASYNC_ACTION_EXAMPLE_SCRIPT_NAME

DEFAULT_CASE_TAG_TO_WAIT_FOR = "Async"

SUCCESS_MESSAGE = 'The following cases have tag "{tag}": {case_ids}'
PENDING_MESSAGE = 'Action is waiting for the cases "{case_ids}" to have a tag {tag}...'
TIMEOUT_ERROR_MESSAGE = (
    "Action ran into a timeout during execution. Please increase the timeout in IDE."
)


class AsyncActionExample(BaseAction):
    def __init__(self):
        super().__init__(ASYNC_ACTION_EXAMPLE_SCRIPT_NAME)
        self.output_message: str = ""
        self.result_value: bool = False
        self.error_output_message: str = (
            f'Error executing action "{ASYNC_ACTION_EXAMPLE_SCRIPT_NAME}".'
        )
        self.cases_with_tag: set[int] = set()
        self.waiting_cases: set[int] = set()

    def _is_approaching_async_timeout(self) -> bool:
        """Determine whether the action approaches asynchronous timeout."""
        return is_approaching_action_timeout(
            self.soar_action.async_total_duration_deadline,
        )

    def _extract_action_parameters(self):
        self.params.case_ids = extract_action_param(
            self.soar_action,
            param_name="Case IDs",
            print_value=True,
        )
        self.params.case_tag_to_wait_for = extract_action_param(
            self.soar_action,
            param_name="Case Tag To Wait For",
            is_mandatory=True,
            default_value=DEFAULT_CASE_TAG_TO_WAIT_FOR,
            print_value=True,
        )
        self.params.additional_data = json.loads(
            extract_action_param(self.soar_action, "additional_data", "{}"),
        )

    def _validate_params(self):
        # If no case IDs provided, use the current case ID
        if not self.params.case_ids:
            self.params.case_ids = [self.soar_action.case_id]
            return

        validator = ParameterValidator(self.soar_action)
        self.params.case_ids = validator.validate_csv(
            param_name="Case IDs",
            csv_string=self.params.case_ids,
        )

    def _is_timeout_approaching(self) -> bool:
        """Check if the action is approaching timeout."""
        # Check if we're within 10% of the timeout
        current_time = unix_now()
        execution_time = current_time - self.action_start_time
        timeout = (
            self.soar_action.execution_deadline_unix_time_ms - self.action_start_time
        )

        return execution_time > (timeout * 0.9)

    def _check_case_tags(self, case_ids: List[str], tag: str) -> dict[int, bool]:
        """Check if the specified cases have the specified tag.

        Args:
                case_ids: List of case IDs to check
                tag: Tag to check for

        Returns:
                Dictionary with case IDs as keys and boolean values indicating
                if they have the tag
        """
        result = {}

        for case_id in case_ids:
            case = get_case_overview_details(
                self.soar_action,
                case_id,
            )
            result[case_id] = tag in case.tags
        return result

    def _first_run(self):
        self._process_cases(self.params.case_ids)

    def _consecutive_run(self):
        self.cases_with_tag.update(
            self.params.additional_data.get("cases_with_tag", [])
        )
        cases_to_process = self.params.additional_data.get("waiting_cases", [])
        self._process_cases(cases_to_process)

    def _process_cases(self, case_ids: Iterable[int]):
        case_tags_status = self._check_case_tags(
            case_ids,
            self.params.case_tag_to_wait_for,
        )
        for case_id, status in case_tags_status.items():
            if status:
                self.cases_with_tag.add(case_id)
                continue
            self.waiting_cases.add(case_id)

    def _perform_action(self, _=None):
        if self._is_approaching_async_timeout():
            raise TimeoutError(TIMEOUT_ERROR_MESSAGE)

        if self.is_first_run:
            self._first_run()
        else:
            self._consecutive_run()

        self.json_results = [
            {"case_id": case_id, "tags": [self.params.case_tag_to_wait_for]}
            for case_id in self.cases_with_tag
        ]

    def _is_all_cases_done(self):
        return self.cases_with_tag == set(self.params.case_ids)

    def _finalize_action_on_success(self) -> None:
        if self._is_all_cases_done():
            self.execution_state = ExecutionState.COMPLETED
            self.result_value = True
            self.output_message = SUCCESS_MESSAGE.format(
                tag=self.params.case_tag_to_wait_for,
                case_ids=", ".join(self.cases_with_tag),
            )
            return

        self.output_message = PENDING_MESSAGE.format(
            case_ids=", ".join(self.waiting_cases), tag=self.params.case_tag_to_wait_for
        )
        self.execution_state = ExecutionState.IN_PROGRESS
        self._result_value = json.dumps({
            "cases_with_tag": self.cases_with_tag,
            "waiting_cases": self.waiting_cases,
        })


def main() -> NoReturn:
    AsyncActionExample().run()


if __name__ == "__main__":
    main()
