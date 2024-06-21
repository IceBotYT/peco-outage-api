"""Main object for getting the PECO outage counter data."""

from __future__ import annotations

from typing import Any

import aiohttp
from pydantic import BaseModel

from .const import (
    ALERTS_URL,
    API_URL,
    COUNTY_LIST,
    PHONE_NUMBER_LENGTH,
    PING_URL,
    PRECHECK_URL,
    QUERY_URL,
    REPORT_URL,
    STATUS_OK,
    TAG_RE,
)


class PecoOutageApi:
    """Main object for getting the PECO outage counter data."""

    def __init__(self) -> None:
        """Initialize the PECO outage counter object."""

    @staticmethod
    async def get_request(
        url: str,
        websession: aiohttp.ClientSession | None = None,
    ) -> dict[str, Any]:
        """Make a GET request to the API."""
        data: dict[str, Any]
        if websession is not None:
            async with websession.get(url) as r:
                data = await r.json()
        else:
            async with aiohttp.ClientSession() as session, session.get(url) as r:
                data = await r.json()

        if r.status != STATUS_OK:
            raise HttpError

        return data

    @staticmethod
    async def post_request(
        url: str,
        data: dict[str, Any],
        websession: aiohttp.ClientSession | None = None,
    ) -> dict[str, Any]:
        """Make a POST request to the API."""
        if websession is not None:
            async with websession.post(url, json=data) as r:
                data = await r.json(content_type="text/html")
        else:
            async with aiohttp.ClientSession() as session, session.post(
                url,
                json=data,
            ) as r:
                data = await r.json(content_type="text/html")

        if r.status != STATUS_OK:
            raise HttpError

        return data

    async def get_outage_count(
        self: PecoOutageApi,
        county: str,
        websession: aiohttp.ClientSession | None = None,
    ) -> OutageResults:
        """Get the outage count for the given county."""

        if county not in COUNTY_LIST:
            raise InvalidCountyError(county)

        data = await self.get_request(API_URL, websession)

        try:
            id_that_has_the_report: str = data["data"]["interval_generation_data"]
        except KeyError as err:
            raise BadJSONError from err

        report_url = REPORT_URL.format(id_that_has_the_report)
        data = await self.get_request(report_url, websession)

        try:
            areas: list[dict[str, Any]] = data["file_data"]["areas"]
        except KeyError as err:
            raise BadJSONError from err

        outage_result: OutageResults = OutageResults(
            customers_out=0,
            percent_customers_out=0,
            outage_count=0,
            customers_served=0,
        )
        for area in areas:
            if area["name"] == county:
                customers_out = area["cust_a"]["val"]
                percent_customers_out = area["percent_cust_a"]["val"]
                outage_count = area["n_out"]
                customers_served = area["cust_s"]
                outage_result = OutageResults(
                    customers_out=customers_out,
                    percent_customers_out=percent_customers_out,
                    outage_count=outage_count,
                    customers_served=customers_served,
                )
        return outage_result

    async def get_outage_totals(
        self: PecoOutageApi,
        websession: aiohttp.ClientSession | None = None,
    ) -> OutageResults:
        """Get the outage totals for the given county and mode."""
        data = await self.get_request(API_URL, websession)

        try:
            id_that_has_the_report: str = data["data"]["interval_generation_data"]
        except KeyError as err:
            raise BadJSONError from err

        report_url = REPORT_URL.format(id_that_has_the_report)
        data = await self.get_request(report_url, websession)

        try:
            totals = data["file_data"]["totals"]
        except KeyError as err:
            raise BadJSONError from err

        return OutageResults(
            customers_out=totals["cust_a"]["val"],
            percent_customers_out=totals["percent_cust_a"]["val"],
            outage_count=totals["n_out"],
            customers_served=totals["cust_s"],
        )

    async def meter_check(
        self: PecoOutageApi,
        phone_number: str,
        websession: aiohttp.ClientSession | None = None,
    ) -> bool:
        """Check if power is being delivered to the house."""
        if len(phone_number) != PHONE_NUMBER_LENGTH:
            msg = "Phone number must be 10 digits"
            raise ValueError(msg)

        if not phone_number.isdigit():
            msg = "Phone number must be numeric"
            raise ValueError(msg)

        data1 = await self.post_request(QUERY_URL, {"phone": phone_number}, websession)

        if not data1["success"]:
            raise HttpError

        if not data1["data"][0]["smartMeterStatus"]:
            raise IncompatibleMeterError

        auid = data1["data"][0]["auid"]
        acc_number = data1["data"][0]["accountNumber"]

        data2 = await self.post_request(
            PRECHECK_URL,
            {
                "auid": auid,
                "accountNumber": acc_number,
                "phone": phone_number,
            },
            websession,
        )

        if not data2["success"]:
            raise HttpError

        if not data2["data"]["meterPing"]:
            raise UnresponsiveMeterError

        data3 = await self.post_request(
            PING_URL,
            {"auid": auid, "accountNumber": acc_number},
            websession,
        )

        if not data3["success"]:
            raise HttpError

        return bool(data3["data"]["meterInfo"]["pingResult"])

    async def get_map_alerts(
        self: PecoOutageApi,
        websession: aiohttp.ClientSession | None = None,
    ) -> AlertResults:
        """Get the alerts that show on the outage map."""
        data = await self.get_request(API_URL, websession)

        try:
            alert_deployment_id: str = data["controlCenter"]["alertDeploymentId"]
        except KeyError as err:
            raise BadJSONError from err

        if alert_deployment_id is None:
            # No alert
            return AlertResults(alert_content="", alert_title="")

        alerts_url = ALERTS_URL.format(alert_deployment_id)
        data1 = await self.get_request(alerts_url, websession)

        # There is always only one alert.
        # Again, if anyone sees more than one alert, please open an issue.
        try:
            alert = data1["_embedded"]["deployedAlertResourceList"][0]["data"][0]
        except KeyError:
            return AlertResults(
                alert_content="",
                alert_title="",
            )

        parsed_content = TAG_RE.sub("", alert["content"].replace("<br />", "\n\n"))

        return AlertResults(
            alert_content=parsed_content,
            alert_title=alert["bannerTitle"],
        )


class OutageResults(BaseModel):
    customers_out: int
    percent_customers_out: int
    outage_count: int
    customers_served: int


class AlertResults(BaseModel):
    alert_content: str
    alert_title: str


class InvalidCountyError(ValueError):
    """Raised when the county is invalid."""

    def __init__(self, county: str) -> None:
        super().__init__(f"{county} is not a valid county")


class HttpError(Exception):
    """Raised when an error during HTTP request occurs."""

    def __init__(self) -> None:
        super().__init__("Bad response from PECO")


class BadJSONError(Exception):
    """Raised when the JSON is invalid."""

    def __init__(self, message: str = "Bad JSON returned from PECO") -> None:
        super().__init__(message)


class MeterError(Exception):
    """Generic meter error."""


class IncompatibleMeterError(MeterError):
    """Raised when the meter is not compatible with the API."""

    def __init__(self) -> None:
        super().__init__("Meter is not compatible with the API")


class UnresponsiveMeterError(MeterError):
    """Raised when the meter is not responding."""

    def __init__(self, message: str = "Meter is not responding") -> None:
        super().__init__(message)
