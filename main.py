import datetime

import aiohttp
import asyncio
import json

from datetime import date, timedelta

from aiohttp import FormData
from colorama import init as colorama_init
from colorama import Fore, Back, Style

from datetime import datetime as dt


async def grid_request(form, header_arg):
    async with aiohttp.ClientSession() as session:
        response = await session.post(
            "https://libcal.lakeheadu.ca/spaces/availability/grid",
            data=form,
            headers=header_arg
        )

        async with response:
            return await response.json()


class Room:
    def __init__(self, eid=None, time_slots=None):
        self.eid = eid
        self.time_slots = time_slots

    def __str__(self):
        return f'EID:{self.eid}, time_slot_size={len(self.time_slots)}'

    def print_timeslots(self):
        string = f'\n{Fore.YELLOW}Room #{self.eid}   ::['
        for time_slot in self.time_slots:
            if 'className' not in time_slot.keys():
                string += f'{Fore.GREEN}\N{FULL BLOCK}'
            else:
                string += f'{Fore.RED}\N{FULL BLOCK}'
        string += f'{Fore.YELLOW}]'
        print(string)

    def print_availability(self):
        left_bound = datetime.datetime(2500, 1, 1)
        right_bound = None
        valid_range = False

        for ts in self.time_slots:
            ts_start_time = dt.fromisoformat(ts.get('start'))

            # If Room Is Free
            if 'className' not in ts:
                if left_bound > ts_start_time:
                    left_bound = ts_start_time
                    right_bound = dt.fromisoformat(ts.get('end'))

                valid_range = True
                right_bound = dt.fromisoformat(ts.get('end'))

            # If Room is taken
            else:
                if valid_range:
                    valid_range = False

                    left_bound_string = dt.strftime(left_bound, "%d %I:%M %p")
                    right_bound_string = dt.strftime(right_bound, "%d %I:%M %p")

                    print(f'    from {left_bound_string} -> {right_bound_string}')
                else:
                    left_bound = datetime.datetime(2500, 1, 1)

        if valid_range:
            left_bound_string = dt.strftime(left_bound, "%I:%M %p")
            right_bound_string = dt.strftime(right_bound, "%I:%M %p")

            print(f'    from {left_bound_string} -> {right_bound_string}')

    # get first timeslots start/end date/time. For every other slot verify it is on the same DAY as start timeslot.
    # and className isn't set. if className is set end date as that slots end date and print range! if day changes do
    # the same but for the last available time, which will be hard coded based on schedule, maybe. or we have to store
    # the previous data...


def option_menu():
    options = {
        1: 'https://libcal.lakeheadu.ca/reserve/',
        2: 'https://libcal.lakeheadu.ca/reserve/ground-floor-study-rooms',
        3: 'https://libcal.lakeheadu.ca/reserve/main-floor-study-rooms',
        4: 'https://libcal.lakeheadu.ca/reserve/fourth-floor-study-rooms'
    }

    print(f'{Fore.GREEN}------------- Select A Room Group -------------')
    print(f'1) All Spaces (Current Bugged)')
    print(f'2) Ground Floor')
    print(f'3) Main Floor')
    print(f'3) Fourth Floor (Bugged, unknown rooms with 10/15min increments display, same with Allspaces)')

    choice = input("Select: ")
    return options[int(choice)]


if __name__ == '__main__':
    colorama_init()

    post_data = dict(lid=437, gid=0, eid=-1, seat=0, seatid=0, zone=0, accessible=0, powered=0,
                     start=dt.fromisoformat("2023-06-12"),
                     end=dt.fromisoformat("2023-06-13"), pageIndex=0, pageSize=18)

    headers = {'Origin': 'https://libcal.lakeheadu.ca'}
    headers.update({'Referer': option_menu()})

    grid_data = FormData(post_data)
    loop = asyncio.get_event_loop()
    grid = loop.run_until_complete(grid_request(grid_data, headers))

    json_object = json.dumps(grid, indent=4)

    # We'll test with a local copy of the response, so we don't spam requests.
    with open("one_day_range.json", "w") as outfile:
        outfile.write(json_object)

    # We now have a list of dicts where each element (dict)
    # is a timeslot.
    slots = grid['slots']
    rooms = [Room()]

    parsed_json = dict()
    room_entry = []

    for slot in slots:
        slot_id = slot.pop('itemId')
        if slot_id != rooms[-1].eid:
            rooms[-1].time_slots = room_entry.copy()
            rooms.append((Room(eid=slot_id)))
            room_entry.clear()
        room_entry.append(slot)
    rooms[-1].time_slots = room_entry.copy()
    rooms.pop(0)

    for room in rooms:
        room.print_timeslots()
        room.print_availability()

# https://library.lakeheadu.ca/r/

"""
Theres some weird items that count in increments of 10 or 15 as well, I dont know why or what rooms they are

"""
