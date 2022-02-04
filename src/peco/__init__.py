"""Main object for getting the PECO outage counter data."""
import aiohttp

from .const import API_URL, COUNTY_LIST, REPORT_URL

class PecoOutageApi:
    """Main object for getting the PECO outage counter data."""
    def __init__(self) -> None:
        """Initialize the PECO outage counter object."""
        pass

    async def get_outage_count(self, county: str, websession: aiohttp.ClientSession = None) -> "dict[str, int]":
        """Get the outage count for the given county."""
        if not isinstance(county, str):
            raise ValueError("County must be specified")

        if county not in COUNTY_LIST:
            raise InvalidCountyError(f"{county} is not a valid county")
    
        if websession is not None:
            async with websession.get(API_URL) as r:
                r: aiohttp.ClientResponse = r
                data: dict = await r.json() # cannot narrow down, unknown response from peco
        else:
            async with aiohttp.ClientSession() as session:
                async with session.get(API_URL) as r:
                    r: aiohttp.ClientResponse = r
                    data: dict = await r.json()

        if r.status != 200:
            raise HttpError("Error getting PECO outage counter data")
        
        try:
            id_that_has_the_report: str = data["data"]["interval_generation_data"]
        except KeyError as err:
            raise BadJSONError("Error getting PECO outage counter data") from err
        
        report_url: str = REPORT_URL.format(id_that_has_the_report)
        if websession is not None:
            async with websession.get(report_url) as r:
                r: aiohttp.ClientResponse = r
                data: dict = await r.json()
        else:
            async with aiohttp.ClientSession() as session:
                async with session.get(report_url) as r:
                    r: aiohttp.ClientResponse = r
                    data: dict = await r.json()
        
        if r.status != 200:
            raise HttpError("Error getting PECO outage counter data")
        
        try:
            areas: list = data["file_data"]["areas"]
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
    async def get_outage_totals(websession: aiohttp.ClientSession = None) -> "dict[str, int]":
        """Get the outage totals for the given county and mode."""
        if websession is not None:
            async with websession.get(API_URL) as r:
                r: aiohttp.ClientResponse = r
                data: dict = await r.json()
        else:
            async with aiohttp.ClientSession() as session:
                async with session.get(API_URL) as r:
                    r: aiohttp.ClientResponse = r
                    data: dict = await r.json()

        if r.status != 200:
            raise HttpError("Error getting PECO outage counter data")

        try:
            id_that_has_the_report: str = data["data"]["interval_generation_data"]
        except KeyError as err:
            raise BadJSONError("Error getting PECO outage counter data") from err
        
        report_url = REPORT_URL.format(id_that_has_the_report)
        if websession is not None:
            async with websession.get(report_url) as r:
                r: aiohttp.ClientResponse = r
                data: dict = await r.json()
        else:
            async with aiohttp.ClientSession() as session:
                async with session.get(report_url) as r:
                    r: aiohttp.ClientResponse = r
                    data: dict = await r.json()
        
        if r.status != 200:
            raise HttpError("Error getting PECO outage counter data")

        try:
            totals: dict = data["file_data"]["totals"]
        except KeyError as err:
            raise BadJSONError("Bad JSON returned from PECO outage counter") from err

        return {
            "customers_out": totals["cust_a"]["val"],
            "percent_customers_out": totals["percent_cust_a"]["val"],
            "outage_count": totals["n_out"],
            "customers_served": totals["cust_s"],
        }


class InvalidCountyError(ValueError):
    """Raised when the county is invalid."""


class HttpError(Exception):
    """Raised when the status code is not 200."""


class BadJSONError(Exception):
    """Raised when the JSON is invalid."""
