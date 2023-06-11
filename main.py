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
            if time_slot.get('available'):
                string += f'{Fore.GREEN}\N{FULL BLOCK}'
            else:
                string += f'{Fore.RED}\N{FULL BLOCK}'
        string += f'{Fore.YELLOW}]'
        print(string, end=' :: ')

    def print_availability(self):
        time_format = "[%m-%d at %I:%M %p]"

        def print_range(start, end):
            start_string = start.strftime(time_format)
            end_string = end.strftime(time_format)
            print(f"From {start_string} -> {end_string}", end=", ")

        available = False
        current_start = None

        for ts in self.time_slots:
            if ts.get('available') and not available:
                available = True
                current_start = datetime.datetime.fromisoformat(ts.get('start'))
            elif not ts.get('available') and available:
                available = False
                print_range(current_start, datetime.datetime.fromisoformat(ts.get('start')))

        if available:
            print_range(current_start, datetime.datetime.fromisoformat(self.time_slots[-1].get('end')))


def option_menu(menu):
    match menu:
        case 1:
            options = {
                1: dict(gid=0),
                2: dict(gid=924),
                3: dict(gid=905),
                4: dict(gid=906),
            }

            print(f'{Fore.GREEN}------------- Select A Room Group -------------')
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

    # This will parse the response into a dict of rooms containing a display name and then a slot.
    while bool(raw_grid):
        entry = parse_timeslot(raw_grid.pop(0))
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


def parse_timeslot(slot):
    """

    :type slot: dict
    """
    availability = True

    if slot.get('className') is not None:
        slot.pop('className')
        availability = False
    slot.update({"available": availability})
    return slot


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

    post_data.update(option_menu(1))
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

    print('------------- Select A Room -------------')
    for i in range(1, len(room_list) + 1):
        print(f'{i}) {room_list[i - 1].name}', end='    ')
        if i % 3 == 0:
            print()  # linebreak
        if i % 9 == 0:
            print()  # linebreak

    i = input("\n\nSelect (*) For All: ")
    if i == '*':
        print_rooms(room_list)
    else:
        i=int(i)
        room_list[i].print_timeslots()
        room_list[i].print_availability()
