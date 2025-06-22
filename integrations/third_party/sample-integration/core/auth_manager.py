import dataclasses

import constants as consts
from exceptions import SampleIntegrationError
from requests import Session
from SiemplifyAction import SiemplifyAction
from SiemplifyConnectors import SiemplifyConnectorExecution
from SiemplifyJob import SiemplifyJob
from TIPCommon.base.utils import CreateSession
from TIPCommon.extraction import extract_script_param
from TIPCommon.types import ChronicleSOAR


@dataclasses.dataclass(frozen=True)
class AuthManagerParams:
    api_root: str
    password: str
    verify_ssl: bool


def build_auth_manager_params(soar_sdk: ChronicleSOAR) -> AuthManagerParams:
    """Extract auth params for Auth manager

    Args:
         soar_sdk: ChronicleSOAR SDK object

    Returns:
        AuthManagerParams: AuthManagerParams object

    """
    if isinstance(soar_sdk, SiemplifyAction):
        input_dictionary = soar_sdk.get_configuration(consts.INTEGRATION_IDENTIFIER)
    elif isinstance(soar_sdk, (SiemplifyConnectorExecution, SiemplifyJob)):
        input_dictionary = soar_sdk.parameters
    else:
        raise SampleIntegrationError(
            "Provided SOAR instance is not supported.",
        )

    api_root = extract_script_param(
        soar_sdk,
        input_dictionary=input_dictionary,
        param_name="API Root",
        default_value=consts.DEFAULT_API_ROOT,
        is_mandatory=True,
        print_value=True,
    )
    password = extract_script_param(
        soar_sdk,
        input_dictionary=input_dictionary,
        param_name="Password Field",
    )
    verify_ssl = extract_script_param(
        soar_sdk,
        input_dictionary=input_dictionary,
        param_name="Verify SSL",
        default_value=consts.DEFAULT_VERIFY_SSL,
        input_type=bool,
        is_mandatory=True,
        print_value=True,
    )

    return AuthManagerParams(
        api_root=api_root,
        password=password,
        verify_ssl=verify_ssl,
    )


class AuthManager:
    def __init__(
        self,
        params: AuthManagerParams,
    ):
        self.params = params
        self.api_root = params.api_root

    def prepare_session(self) -> Session:
        """Preparse session object to be used in API session."""
        session = CreateSession.create_session()
        session.verify = self.params.verify_ssl
        session.headers.update({"dummy-password-header": f"{self.params.password}"})
        return session
