import logging
import re
from typing import Final

API_URL: Final = "https://kubra.io/stormcenter/api/v1/stormcenters/39e6d9f3-fdea-4539-848f-b8631945da6f/views/74de8a50-3f45-4f6a-9483-fd618bb9165d/currentState?preview=false"
REPORT_URL: Final = "https://kubra.io/{}/public/reports/a36a6292-1c55-44de-a6a9-44fedf9482ee_report.json"
COUNTY_LIST: Final = [
    "BUCKS",
    "CHESTER",
    "DELAWARE",
    "MONTGOMERY",
    "PHILADELPHIA",
    "YORK",
]
QUERY_URL: Final = "https://secure.peco.com/.euapi/mobile/custom/anon/PECO/outage/query"
PRECHECK_URL: Final = (
    "https://secure.peco.com/.euapi/mobile/custom/anon/PECO/outage/precheck"
)
PING_URL: Final = "https://secure.peco.com/.euapi/mobile/custom/anon/PECO/outage/ping"
ALERTS_URL: Final = "https://kubra.io/stormcenter/api/v1/stormcenters/39e6d9f3-fdea-4539-848f-b8631945da6f/alerts/deployed?id={}&viewId=74de8a50-3f45-4f6a-9483-fd618bb9165d"
TAG_RE: Final = re.compile(r"<[^>]+>")
LOGGER: Final = logging.getLogger(__package__)
STATUS_OK: Final = 200
PHONE_NUMBER_LENGTH: Final = 10
