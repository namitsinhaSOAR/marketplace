from __future__ import annotations

from soar_sdk.ScriptResult import EXECUTION_STATE_COMPLETED, EXECUTION_STATE_FAILED
from soar_sdk.SiemplifyAction import SiemplifyAction
from soar_sdk.SiemplifyUtils import output_handler

from ..core.Constants import (
    GET_ALL_SERVICES_SCRIPT_NAME,
    INTEGRATION_DISPLAY_NAME,
    INTEGRATION_NAME,
)
from ..core.VorlonManager import VorlonManager


@output_handler
def main():
    siemplify = SiemplifyAction()
    siemplify.script_name = GET_ALL_SERVICES_SCRIPT_NAME
    siemplify.LOGGER.info("----------------- Main - Param Init -----------------")

    api_root = siemplify.extract_configuration_param(
        provider_name=INTEGRATION_NAME,
        param_name="API Root",
    )
    client_id = siemplify.extract_configuration_param(
        provider_name=INTEGRATION_NAME,
        param_name="Client ID",
    )
    client_secret = siemplify.extract_configuration_param(
        provider_name=INTEGRATION_NAME,
        param_name="Client Secret",
    )

    siemplify.LOGGER.info("----------------- Main - Started -----------------")
    try:
        manager = VorlonManager(
            url=api_root,
            client_id=client_id,
            client_secret=client_secret,
        )
        services = manager.get_all_services()
        siemplify.result.add_result_json(services)
        result = True
        status = EXECUTION_STATE_COMPLETED
        output_message = f"Successfully fetched all services from the {INTEGRATION_DISPLAY_NAME} server"

    except Exception as e:
        result = False
        status = EXECUTION_STATE_FAILED
        output_message = (
            f"Failed to fetch services from {INTEGRATION_DISPLAY_NAME} server! {e}"
        )

    siemplify.LOGGER.info("----------------- Main - Finished -----------------")
    siemplify.LOGGER.info(f"Status: {status}")
    siemplify.LOGGER.info(f"Result: {result}")
    siemplify.LOGGER.info(f"Output Message: {output_message}")

    siemplify.end(output_message, result, status)


if __name__ == "__main__":
    main()
