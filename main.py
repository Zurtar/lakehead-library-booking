import datetime

import aiohttp
import asyncio
import json


from aiohttp import FormData
from colorama import init as colorama_init
from colorama import Fore, Back, Style

from datetime import datetime as dt


'''
TODO:
    - General cleanup
    - Right now we just get the times, build an actual booking request
    - Add confirmation portion.
    - General UI Improvement..
    - 
'''





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
    def __init__(self, name=None, id=None, time_slots=None):
        self.name = name
        self.id = id
        self.time_slots = time_slots

    def __str__(self):
        return f'EID:{self.id}, time_slot_size={len(self.time_slots)}'

    def print_timeslots(self):
        string = f'\n{Fore.YELLOW} {self.name}   ::['
        for time_slot in self.time_slots:
            if 'className' not in time_slot.keys():
                string += f'{Fore.GREEN}\N{FULL BLOCK}'
            else:
                string += f'{Fore.RED}\N{FULL BLOCK}'
        string += f'{Fore.YELLOW}]'
        print(string, end=' :: ')

    def print_availability(self):
        time_format = "[%m-%d at %I:%M %p]"

        left_bound = datetime.datetime(2500, 1, 1)
        right_bound = None
        valid_range = False

        for ts in self.time_slots:
            ts_start_time = dt.fromisoformat(ts.get('start'))

            # If Room Is Free
            if 'className' not in ts:
                if left_bound > ts_start_time:
                    left_bound = ts_start_time

                valid_range = True
                right_bound = dt.fromisoformat(ts.get('end'))

            # If Room is taken
            else:
                if valid_range:
                    valid_range = False

                    left_bound_string = dt.strftime(left_bound, time_format)
                    right_bound_string = dt.strftime(right_bound, time_format)

                    print(f'from {left_bound_string} -> {right_bound_string}', end=', ')
                else:
                    left_bound = datetime.datetime(2500, 1, 1)

        if valid_range:
            left_bound_string = dt.strftime(left_bound, time_format)
            right_bound_string = dt.strftime(right_bound, time_format)

            print(f'from {left_bound_string} -> {right_bound_string}', end=', ')

    # get first timeslots start/end date/time. For every other slot verify it is on the same DAY as start timeslot.
    # and className isn't set. if className is set end date as that slots end date and print range! if day changes do
    # the same but for the last available time, which will be hard coded based on schedule, maybe. or we have to store
    # the previous data...


def option_menu():
    options = {
        1: dict(gid=0),
        2: dict(gid=924),
        3: dict(gid=905),
        4: dict(gid=906),
    }

    print(f'{Fore.GREEN}------------- Select A Room Group -------------')
    print(f'--- Bug: unknown rooms with 10/15min increments display ---')
    print(f'1) All Spaces')
    print(f'2) Ground Floor')
    print(f'3) Main Floor')
    print(f'4) Fourth Floor')

    choice = input("Select: ")
    return options[int(choice)]

def parse_json_response(raw_grid):
    """
    :type raw_grid: list
    """
    # Dictionary that will hold our parsed json datat
    parsed_json = dict()

    # Load our Display names for rooms
    name_file = open('room_names.json')
    room_names_json = json.load(name_file)
    room_names_all = room_names_json.get('all_rooms')
    # room_names_invalid = room_names_json.get('ignore_list')

    entries = []
    start_id = raw_grid[0].get('itemId')

    while bool(raw_grid):
        entry = raw_grid.pop(0)
        entry_id = entry.pop('itemId')

        if entry_id != start_id:
            parsed_json.update({
                start_id: {'name': room_names_all.get(str(start_id)), 'slots': entries.copy()}
            })
            start_id = entry_id
            entries.clear()

        entries.append(entry)

    parsed_json.update({
        start_id: {'name': room_names_all.get(str(start_id)), 'slots': entries.copy()}
    })

    # Trim ignored keys.
    # for key in room_names_invalid.keys():
    #    parsed_json.pop(int(key), None)

    with open("parsed_response.json", "w") as parsed_file:
        parsed_file.write(json.dumps(parsed_json, indent=4))

    parsed_file.close()
    name_file.close()

    return parsed_json

def build_rooms(parsed_grid):
    room_list = []
    for room_id in parsed_grid.keys():
        room_entry = parsed_grid.get(room_id)

        # If we have a display name for the room use that otherwise it uses its raw room_id (Ternary opp.)
        room_name = (room_entry.get('name'), room_id)[room_entry.get('name') is None]

        room_list.append(Room(
            name=room_name,
            id=room_id,
            time_slots=room_entry.get('slots')
        ))
    return room_list

def print_rooms(room_list):
    for room in room_list:
        room.print_timeslots()
        room.print_availability()
    print(f'\nRooms: {len(room_list)}')

def dump_raw_response(to_write):
    raw_grid_json = json.dumps(to_write, indent=4)
    with open("raw_response.json", "w") as outfile:
        outfile.write(raw_grid_json)
    outfile.close()


if __name__ == '__main__':
    colorama_init()

    post_data = dict(lid=437, gid=0, eid=-1, seat=0, seatid=0, zone=0, accessible=0, powered=0,
                     start=dt.fromisoformat("2023-06-12"),
                     end=dt.fromisoformat("2023-06-13"), pageIndex=0, pageSize=18)

    headers = {'Origin': 'https://libcal.lakeheadu.ca'}
    headers.update({'Referer': 'https://libcal.lakeheadu.ca/spaces?lid=437&gid=0&c=0'})

    post_data.update(option_menu())
    grid_data = FormData(post_data)

    # Not really needed we can do a non async request because we wait for it anyway.
    grid = asyncio.run(grid_request(grid_data, headers))

    # hacky awful way to handle a empty response
    if len(grid['slots']) < 1:
        print("Empty Response? Maybe no bookings avaliable....")
        print(f'Request Data: {post_data}')
        print(f'Headers Data: {headers}')
        exit(1)

    dump_raw_response(grid)
    parsed_json = parse_json_response(grid['slots'])

    room_list = build_rooms(parsed_json)
    print_rooms(room_list)


