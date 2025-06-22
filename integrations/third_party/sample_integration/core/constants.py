import datetime
from enum import Enum

# Integration Identifiers
INTEGRATION_IDENTIFIER = "SampleIntegration"
INTEGRATION_DISPLAY_NAME = "Sample Integration"

# Script Identifiers
PING_SCRIPT_NAME = f"{INTEGRATION_IDENTIFIER} - Ping"
SIMPLE_ACTION_EXAMPLE_SCRIPT_NAME = f"{INTEGRATION_IDENTIFIER} - Simple Action Example"

# Default Configuration Parameter Values
DEFAULT_API_ROOT = "https://api.vatcomply.com"
DEFAULT_VERIFY_SSL = True

# API Constants
ENDPOINTS = {
    "ping": "/rates",
    "get-base-rate": "/rates",
}
REQUEST_TIMEOUT = 30


# Parameter Values
class DDLEnum(Enum):
    @classmethod
    def values(cls) -> list[str]:
        return [item.value for item in cls]


class CurrenciesDDLEnum(DDLEnum):
    SELECT_ONE = "Select One"
    USD = "USD"
    EUR = "EUR"
    CAD = "CAD"


class TimeFrameDDLEnum(DDLEnum):
    TODAY = "Today"
    LAST_WEEK = "Last 7 Days"
    CUSTOM = "Custom"

    def to_start_date(self) -> datetime.date:
        match self:
            case TimeFrameDDLEnum.TODAY:
                return datetime.date.today()
            case TimeFrameDDLEnum.LAST_WEEK:
                return datetime.date.today() - datetime.timedelta(days=7)
            case _:
                raise ValueError(
                    f"Cannot convert object {self} to Date object",
                )
