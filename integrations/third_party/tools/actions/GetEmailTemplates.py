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

import json

from soar_sdk.ScriptResult import EXECUTION_STATE_COMPLETED
from soar_sdk.SiemplifyAction import SiemplifyAction
from soar_sdk.SiemplifyUtils import output_handler

GET_TEMPLATE_URL = "{}/external/v1/settings/GetEmailTemplateRecords?format=camel"


@output_handler
def main():
    siemplify = SiemplifyAction()
    siemplify.SCRIPT_NAME = "Get Email Templates"

    template_type = siemplify.extract_action_param("Template Type", print_value=True)

    status = EXECUTION_STATE_COMPLETED  # used to flag back to siemplify system, the action final status
    output_message = (
        "output message :"  # human readable message, showed in UI as the action result
    )
    result_value = (
        None  # Set a simple result value, used for playbook if\else and placeholders.
    )

    email_templates = siemplify.session.get(GET_TEMPLATE_URL.format(siemplify.API_ROOT))
    email_templates.raise_for_status()
    res = []
    for template in email_templates.json():
        if (template["type"] == 1 and template_type == "HTML") or (
            template["type"] == 0 and template_type == "Standard"
        ):
            res.append(template)
    siemplify.result.add_result_json({"templates": res})
    siemplify.end(output_message, json.dumps(res), status)


if __name__ == "__main__":
    main()
