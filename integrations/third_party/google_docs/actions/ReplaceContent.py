from __future__ import annotations

import json

from soar_sdk.SiemplifyAction import SiemplifyAction
from soar_sdk.SiemplifyUtils import output_handler

from ..core.GoogleDocsManager import GoogleDocsManager

IDENTIFIER = "Google Docs"


@output_handler
def main():
    siemplify = SiemplifyAction()

    credentials_json = siemplify.extract_configuration_param(
        IDENTIFIER,
        "Credentials Json",
    )

    document_id = siemplify.extract_action_param(
        param_name="Document Id",
        is_mandatory=True,
    )
    json_str = siemplify.extract_action_param(param_name="Json", is_mandatory=True)

    json_object = json.loads(json_str)
    items = json_object["items"]
    requests = []

    for item in items:
        text_to_search = item["text_to_search"]
        text_to_replace = item["text_to_replace"]
        match_case = item["match_case"]

        item_to_replace = {
            "replaceAllText": {
                "containsText": {"text": text_to_search, "matchCase": match_case},
                "replaceText": text_to_replace,
            },
        }
        requests.append(item_to_replace)

    google_doc_manager = GoogleDocsManager(credentials_json)
    res = google_doc_manager.execute_request(document_id, requests)

    siemplify.result.add_result_json(res)

    siemplify.end("Content was successfully replaced", document_id)


if __name__ == "__main__":
    main()
