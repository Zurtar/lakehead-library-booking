import aiohttp
import asyncio
from datetime import date, timedelta

from aiohttp import *


async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()


async def grid_request(form, header_arg):
    async with aiohttp.ClientSession() as session:
        response = await session.post(
            "https://libcal.lakeheadu.ca/spaces/availability/grid",
            data=form,
            headers=header_arg
        )

        async with response:
            return await response.json()


if __name__ == '__main__':
    str(date.today())

    post_data = dict(
        lid=437,
        gid=0,
        eid=-1,
        seat=0,
        seatid=0,
        zone=0,
        accessible=0,
        powered=0,
        start=str(date.today()),
        end=str(date.today() + timedelta(days=5)),
        pageIndex=0,
        pageSize=18
    )

    headers = {
        'Origin': 'https://libcal.lakeheadu.ca',
        'Referer': 'https://libcal.lakeheadu.ca/spaces?lid=437&gid=0&c=0'
    }

    grid_data = FormData(post_data)

    loop = asyncio.get_event_loop()
    grid = loop.run_until_complete(grid_request(grid_data, headers))

    #Now we have to parse the json response!

# https://library.lakeheadu.ca/r/
