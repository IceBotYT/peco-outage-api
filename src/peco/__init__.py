"""Main object for getting the PECO outage counter data."""
from __future__ import annotations

from typing import Any
import aiohttp

from .const import API_URL, COUNTY_LIST, REPORT_URL, PRECHECK_URL, QUERY_URL, PING_URL

class PecoOutageApi:
    """Main object for getting the PECO outage counter data."""
    def __init__(self) -> None:
        """Initialize the PECO outage counter object."""
        pass

    async def get_outage_count(self, county: str, websession: aiohttp.ClientSession | None=None) -> dict[str, int]:
        """Get the outage count for the given county."""

        if county not in COUNTY_LIST:
            raise InvalidCountyError(f"{county} is not a valid county")
    
        if websession is not None:
            async with websession.get(API_URL) as r:
                data = await r.json()
        else:
            async with aiohttp.ClientSession() as session:
                async with session.get(API_URL) as r:
                    data = await r.json()

        if r.status != 200:
            raise HttpError("Error getting PECO outage counter data")
        
        try:
            id_that_has_the_report: str = data["data"]["interval_generation_data"]
        except KeyError as err:
            raise BadJSONError("Error getting PECO outage counter data") from err
        
        report_url = REPORT_URL.format(id_that_has_the_report)
        if websession is not None:
            async with websession.get(report_url) as r:
                data = await r.json()
        else:
            async with aiohttp.ClientSession() as session:
                async with session.get(report_url) as r:
                    data = await r.json()
        
        if r.status != 200:
            raise HttpError("Error getting PECO outage counter data")
        
        try:
            areas: list[dict[str, Any]] = data["file_data"]["areas"]
        except KeyError as err:
            raise BadJSONError("Bad JSON returned from PECO outage counter") from err

        outage_dict = {}
        for area in areas:
            if area["name"] == county:
                customers_out: int = area["cust_a"]["val"]
                percent_customers_out: int = area["percent_cust_a"]["val"]
                outage_count: int = area["n_out"]
                customers_served: int = area["cust_s"]
                outage_dict = {
                    "customers_out": customers_out,
                    "percent_customers_out": percent_customers_out,
                    "outage_count": outage_count,
                    "customers_served": customers_served,
                }
        return outage_dict

    @staticmethod
    async def get_outage_totals(websession: aiohttp.ClientSession | None=None) -> dict[str, int]:
        """Get the outage totals for the given county and mode."""
        if websession is not None:
            async with websession.get(API_URL) as r:
                data = await r.json()
        else:
            async with aiohttp.ClientSession() as session:
                async with session.get(API_URL) as r:
                    data = await r.json()

        if r.status != 200:
            raise HttpError("Error getting PECO outage counter data")

        try:
            id_that_has_the_report: str = data["data"]["interval_generation_data"]
        except KeyError as err:
            raise BadJSONError("Error getting PECO outage counter data") from err
        
        report_url = REPORT_URL.format(id_that_has_the_report)
        if websession is not None:
            async with websession.get(report_url) as r:
                data = await r.json()
        else:
            async with aiohttp.ClientSession() as session:
                async with session.get(report_url) as r:
                    data = await r.json()
        
        if r.status != 200:
            raise HttpError("Error getting PECO outage counter data")

        try:
            totals = data["file_data"]["totals"]
        except KeyError as err:
            raise BadJSONError("Bad JSON returned from PECO outage counter") from err

        return {
            "customers_out": totals["cust_a"]["val"],
            "percent_customers_out": totals["percent_cust_a"]["val"],
            "outage_count": totals["n_out"],
            "customers_served": totals["cust_s"],
        }
    
    @staticmethod
    async def meter_check(phone_number: str, websession: aiohttp.ClientSession | None=None) -> bool:
        """Check if power is being delivered to the house."""
        if len(phone_number) != 10:
            raise ValueError("Phone number must be 10 digits")
        
        if not phone_number.isdigit():
            raise ValueError("Phone number must be numeric")
        
        data1: dict[str, Any]
        if websession is not None:
            async with websession.post(QUERY_URL, json={"phone": phone_number}) as response:
                data1 = await response.json(content_type='text/html')
        else:
            async with aiohttp.ClientSession() as session:
                async with session.post(QUERY_URL, json={"phone": phone_number}) as response:
                    data1 = await response.json(content_type='text/html')

        if data1["success"] != True:
            raise HttpError("Error checking meter")
        
        if data1["data"][0]["smartMeterStatus"] == False:
            raise IncompatibleMeterError("Meter is not compatible with smart meter checking")
        
        auid = data1["data"][0]["auid"]
        acc_number = data1["data"][0]["accountNumber"]

        data2: dict[str, Any]
        if websession is not None:
            async with websession.post(PRECHECK_URL, json={"auid": auid, "accountNumber": acc_number, "phone": phone_number}) as response:
                data2 = await response.json(content_type='text/html')
        else:
            async with aiohttp.ClientSession() as session:
                async with session.post(PRECHECK_URL, json={"auid": auid, "accountNumber": acc_number, "phone": phone_number}) as response:
                    data2 = await response.json(content_type='text/html')
        
        if data2["success"] != True:
            raise HttpError("Error checking meter")
        
        if data2["data"]["meterPing"] == False:
            raise UnresponsiveMeterError("Meter is not responding")
        
        ping_result: bool
        if websession is not None:
            async with websession.post(PING_URL, json={"auid": auid, "accountNumber": acc_number}) as response:
                data3 = await response.json(content_type='text/html')
                if data3["success"] != True:
                    raise HttpError("Error checking meter")
                ping_result = bool(data3["data"]["meterInfo"]["pingResult"])
        else:
            async with aiohttp.ClientSession() as session:
                async with session.post(PING_URL, json={"auid": auid, "accountNumber": acc_number}) as response:
                    data3 = await response.json(content_type='text/html')
                    if data3["success"] != True:
                        raise HttpError("Error checking meter")
                    ping_result = bool(data3["data"]["meterInfo"]["pingResult"])
        
        return ping_result
        

class InvalidCountyError(ValueError):
    """Raised when the county is invalid."""

class HttpError(Exception):
    """Raised when the status code is not 200."""

class BadJSONError(Exception):
    """Raised when the JSON is invalid."""

class MeterError(Exception):
    """Generic meter error."""
class IncompatibleMeterError(MeterError):
    """Raised when the meter is not compatible with the API."""

class UnresponsiveMeterError(MeterError):
    """Raised when the meter is not responding."""

