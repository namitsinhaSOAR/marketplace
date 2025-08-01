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

import datetime
import sys

import arrow
import croniter
from soar_sdk.ScriptResult import EXECUTION_STATE_COMPLETED, EXECUTION_STATE_INPROGRESS
from soar_sdk.SiemplifyAction import SiemplifyAction

SCRIPT_NAME = "Siemplify - Delay Playbook V2"


def main():
    siemplify = SiemplifyAction()
    siemplify.script_name = SCRIPT_NAME
    seconds = int(siemplify.parameters.get("Seconds", 0))
    minutes = int(siemplify.parameters.get("Minutes", 0))
    hours = int(siemplify.parameters.get("Hours", 0))
    days = int(siemplify.parameters.get("Days", 0))
    cron_expression = siemplify.parameters.get("Cron Expression")

    if cron_expression:
        now = arrow.utcnow().datetime
        cron = croniter.croniter(cron_expression, now)
        next_timestamp = cron.get_next(datetime.datetime)
        if now < next_timestamp:
            siemplify.LOGGER.info(
                f"Cron expression not matched, waiting until {next_timestamp.isoformat()}",
            )
            siemplify.end(
                f"Hasn't reached the desired date {next_timestamp.isoformat()}. Current date: {now.isoformat()}",
                next_timestamp.isoformat(),
                EXECUTION_STATE_INPROGRESS,
            )
        else:
            siemplify.LOGGER.info("Cron expression matched, finishing waiting")
            siemplify.end(
                f"Reached target date {next_timestamp.isoformat()}",
                "true",
                EXECUTION_STATE_COMPLETED,
            )

    target_date = arrow.utcnow().shift(
        seconds=seconds,
        minutes=minutes,
        hours=hours,
        days=days,
    )

    siemplify.LOGGER.info(f"Waiting until {target_date.isoformat()!s}")

    if target_date <= arrow.utcnow():
        # Reached target date
        siemplify.LOGGER.info(f"Reached target date {target_date.isoformat()}")
        siemplify.end(
            f"Reached target date {target_date.isoformat()}",
            "true",
            EXECUTION_STATE_COMPLETED,
        )

    else:
        siemplify.LOGGER.info(
            f"Hasn't reached the desired date {target_date.isoformat()}. Current date: {arrow.utcnow().isoformat()}",
        )
        siemplify.end(
            f"Hasn't reached the desired date {target_date.isoformat()}",
            target_date.isoformat(),
            EXECUTION_STATE_INPROGRESS,
        )


def wait():
    siemplify = SiemplifyAction()
    siemplify.script_name = SCRIPT_NAME
    try:
        target_date = arrow.get(siemplify.parameters["additional_data"])
    except:  # order matters!
        try:
            target_date = arrow.get(
                siemplify.parameters["additional_data"],
                "M/D/YYYY H:mm:ss A",
            )
        except:
            try:
                target_date = arrow.get(
                    siemplify.parameters["additional_data"],
                    "M/D/YYYY HH:mm:ss A",
                )
            except:
                target_date = arrow.get(
                    siemplify.parameters["additional_data"],
                    "M/D/YYYY HH:mm:ss",
                )
    cron_expression = siemplify.parameters.get("Cron Expression")
    if cron_expression:
        now = arrow.utcnow().datetime
        if now < target_date:
            siemplify.LOGGER.info(
                f"Cron expression not matched, waiting until {target_date.isoformat()}",
            )
            siemplify.end(
                f"Hasn't reached the desired date {target_date.isoformat()}. Current date: {now.isoformat()}",
                target_date.isoformat(),
                EXECUTION_STATE_INPROGRESS,
            )
        else:
            siemplify.LOGGER.info("Cron expression matched, finishing waiting")
            siemplify.end(
                f"Reached target date {target_date.isoformat()}",
                "true",
                EXECUTION_STATE_COMPLETED,
            )

    if target_date <= arrow.utcnow():
        # Reached target date
        siemplify.LOGGER.info(f"Reached target date {target_date.isoformat()}")
        siemplify.end(
            f"Reached target date {target_date.isoformat()}",
            "true",
            EXECUTION_STATE_COMPLETED,
        )

    else:
        siemplify.LOGGER.info(
            f"Hasn't reached the desired date {target_date.isoformat()}. Current date: {arrow.utcnow().isoformat()}",
        )
        siemplify.end(
            f"Hasn't reached the desired date {target_date.isoformat()}",
            target_date.isoformat(),
            EXECUTION_STATE_INPROGRESS,
        )


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[2] == "True":
        main()
    else:
        wait()
