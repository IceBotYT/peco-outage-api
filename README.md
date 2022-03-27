# PECO Outage API

A library for interacting with the [PECO outage map](https://www.peco.com/Outages/CheckOutageStatus/Pages/OutageMap.aspx) to gain the numbers from it.

Interacting with the API is simple.

```python
from peco import PecoOutageApi

async def get_data():
    api = PecoOutageApi()
    # How many customers are affected by an outage in Bucks county?
    print(await api.get_outage_count('BUCKS').customers_out)

    # What is the total outage count for the entire region?
    print(await api.get_outage_totals().outage_count)

    # What is the percentage of customers that are affected by an outage?
    print(await api.get_outage_totals().percent_customers_out)

import asyncio
asyncio.run(get_data())
```

*Note:* The `percent_customers_out` key does not go below 5%. It will show up as `4.999999` instead. Make sure to take this into account when using the API.

The counties that are available are:
- BUCKS
- CHESTER
- DELAWARE
- MONTGOMERY
- PHILADELPHIA
- YORK

The values you can access are:
- customers_out
- percent_customers_out
- outage_count
- customers_served
