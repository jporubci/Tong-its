#!/usr/bin/env python3
# lobby.py

# To read stdin and write stdout without blocking 
import curses

# To handle connections and messages asynchronously
import asyncio

# To get host address and port
import socket

# To get catalog
import http.client

# os.getlogin() to get username
import os

# To send and receive data structures via messages
import json

# time.time_ns() to date messages
import time

# Predefined constants
from config import Settings

# Host
from host import Host

# Client
from client import Client


# Host a lobby
async def hostState(state_info):
    
    # Listen for user input
    char = -1
    while char == -1:
        await asyncio.sleep(0)
        
        # Refresh if needed
        if state_info.handle.refresh_flag.is_set():
            state_info.handle.refresh_flag.clear()
            await state_info.get_lobbies()
            
        char = state_info.stdscr.getch()
    
    if chr(char) != '\n':
        # Update internal buffer
        # '\x7f' is backspace, i don't know why
        if chr(char) == '\x7f' and state_info.input_buffer != '':
            state_info.input_buffer = state_info.input_buffer[:-1]
        elif chr(char).isalnum():
            state_info.input_buffer += chr(char)
        
        return state_info
    
    # Parse user input
    choice = state_info.input_buffer
    state_info.input_buffer = ''
    state_info.stdscr.addch('\n')
    state_info.stdscr.refresh()
    
    await state_info.handle.clients_lock.acquire()
    
    # Parse user input
    if not choice.isnumeric() or int(choice) > len(state_info.handle.clients) or choice == '0':
        
        state_info.handle.clients_lock.release()
        
        if choice == 'r':
            state_info.handle.refresh_flag.clear()
            await state_info.get_lobbies()
        
        elif choice == 'd':
            # Shutdown host
            await state_info.handle.shutdown()
            
            # Refresh lobbies after shutdown
            await state_info.get_lobbies()
            
            # Return to menu
            state_info.curr_state = 'MENU'
        
        elif choice == 's':
            # TODO: Implement start
            pass
        
        elif choice == 'q':
            # Shutdown host
            await state_info.handle.shutdown()
            
            # Return to menu
            state_info.curr_state = 'QUIT'
        
        return state_info
        
    # Kick client
    clients_copy = [client for client in self.handle.clients]
    clients_copy.sort(key=lambda x: x['join_time'])
    client = clients_copy[int(choice) - 1]
    
    # Send kick
    await state_info.handle.send_message(client[1], {'command': 'kick'})
    
    # Trigger shutdown in client handler
    state_info.handle.clients[client].shutdown_flag.set()
    
    return state_info


async def displayHost(state_info):
    
    if state_info.lobbies == None:
        state_info.curr_state = 'QUIT'
        # Shutdown host
        await state_info.handle.shutdown()
        return
    
    # Display lobbies (without an index)
    state_info.display_lobbies()
    
    # Display own lobby and kick options
    state_info.stdscr.addch('\n')
    state_info.stdscr.addstr(f'{state_info.name}\n')
    async with self.clients_lock:
        clients_copy = [self.clients[client] for client in self.clients]
    clients_copy.sort(key=lambda x: x['join_time'])
    client_names = [client['name'] for client in clients_copy]
    for i, client_name in enumerate(client_names, start=1):
        state_info.stdscr.addstr(f'{i}: {client_name}\n')
    state_info.stdscr.addch('\n')
    
    # Display options
    state_info.stdscr.addstr('r: refresh\n')
    state_info.stdscr.addstr('d: disband\n')
    state_info.stdscr.addstr('s: start\n')
    state_info.stdscr.addstr('q: quit\n')
    
    # Display prompt
    state_info.stdscr.addstr(f'\n> {state_info.input_buffer}')


async def joinState(state_info):
    
    # Listen for user input
    char = -1
    while char == -1:
        await asyncio.sleep(0)
        
        # Refresh if needed
        if state_info.handle.refresh_flag.is_set():
            state_info.handle.refresh_flag.clear()
            await state_info.get_lobbies()
            
        char = state_info.stdscr.getch()
    
    if chr(char) != '\n':
        # Update internal buffer
        # '\x7f' is backspace, i don't know why
        if chr(char) == '\x7f' and state_info.input_buffer != '':
            state_info.input_buffer = state_info.input_buffer[:-1]
        elif chr(char).isalnum():
            state_info.input_buffer += chr(char)
        
        return state_info
    
    # Parse user input
    choice = state_info.input_buffer
    state_info.input_buffer = ''
    state_info.stdscr.addch('\n')
    state_info.stdscr.refresh()
    
    # Parse user input
    if choice == 'r':
        state_info.handle.refresh_flag.clear()
        await state_info.get_lobbies()
        
        # Get client names
        await self.send_message(state_info.handle.writer, {'command': 'get_client_names'})
    
    elif choice == 'l':
        # Send leave message to host
        state_info.handle.send_message(state_info.handle.writer, {'command': 'leave'})
        
        await state_info.handle.shutdown()
        
        await state_info.get_lobbies()
        
        state_info.curr_state = 'MENU'
    
    elif choice == 'q':
        # Send leave message to host
        state_info.handle.send_message(state_info.handle.writer, {'command': 'leave'})
        
        await state_info.handle.shutdown()
        
        state_info.curr_state = 'QUIT'
    
    return state_info


async def displayJoin(state_info):
    
    # Check lobbies
    if state_info.lobbies == None:
        await state_info.handle.shutdown()
        state_info.curr_state = 'QUIT'
        return
    
    # Check client names
    if state_info.client_names == None:
        await state_info.handle.shutdown()
        state_info.curr_state = 'MENU'
        return
    
    # Display lobbies
    state_info.display_lobbies()
    
    # Display host name
    state_info.stdscr.addch('\n')
    state_info.stdscr.addstr(f'{state_info.host_name}\n')
    
    # Display client names
    for client_name in state_info.client_names:
        state_info.stdscr.addstr(f'{client_name}\n')
    state_info.stdscr.addch('\n')
    
    # Display options
    state_info.stdscr.addstr('r: refresh\n')
    state_info.stdscr.addstr('l: leave\n')
    state_info.stdscr.addstr('q: quit\n')
    
    # Display prompt
    state_info.stdscr.addstr(f'\n> {state_info.input_buffer}')


async def menuState(state_info):
    
    # Listen for user input
    char = -1
    while char == -1:
        await asyncio.sleep(0)
        char = state_info.stdscr.getch()
    
    if chr(char) != '\n':
        # Update internal buffer
        # '\x7f' is backspace, i don't know why
        if chr(char) == '\x7f' and state_info.input_buffer != '':
            state_info.input_buffer = state_info.input_buffer[:-1]
        elif chr(char).isalnum():
            state_info.input_buffer += chr(char)
        
        return state_info
    
    # Parse user input
    choice = state_info.input_buffer
    state_info.input_buffer = ''
    state_info.stdscr.addch('\n')
    state_info.stdscr.refresh()
    
    if not choice.isnumeric() or int(choice) > len(state_info.lobbies):
        
        if choice == 'r':
            await state_info.get_lobbies()
            
        elif choice == 'q':
            state_info.curr_state = 'QUIT'
        
        return state_info
    
    if choice == '0':
        state_info.handle = Host()
        
        # Create server object
        state_info.handle.server = await asyncio.start_server(state_info.handle.handle_client, host=socket.gethostname(), backlog=state_info.settings.MAX_CLIENTS)
        
        # Try to register with catalog server
        state_info.handle.register()
        
        # Register every REGISTER_INTERVAL seconds
        state_info.handle.register_task = asyncio.create_task(state_info.handle.register_task())
        
        # Check all pings every PING_INTERVAL seconds
        state_info.handle.purge_task = asyncio.create_task(state_info.handle.purge_task())
        
        # Get lobbies (should see self in list of lobbies)
        state_info.handle.refresh_flag.clear()
        await state_info.get_lobbies()
        
        state_info.curr_state = 'HOST'
        
        return state_info
    
    state_info.handle = Client()
    
    # Save lobby choice
    state_info.handle.host_name = state_info.lobbies[int(choice) - 1]['owner']
    
    # Try to connect to chosen lobby
    state_info.handle.reader, state_info.handle.writer = await asyncio.open_connection(state_info.lobbies[int(choice) - 1]['address'], state_info.lobbies[int(choice) - 1]['port'])
    
    # Send name to host
    await state_info.handle.send_message(state_info.handle.writer, {'command': 'join', 'name': state_info.name})
    
    # Get response
    response = await state_info.handle.get_message(state_info.handle.reader)
    
    # Parse response
    if response['status'] == 'success':
        
        # Listen to host for refresh requests or kicks
        state_info.handle.listen_task = asyncio.create_task(state_info.handle.listen_task())
        
        # Register every PING_INTERVAL seconds
        state_info.ping_task = asyncio.create_task(state_info.ping_task())
        
        state_info.curr_state = 'JOIN'
        
        return state_info
    
    # Error joining lobby
    await state_info.handle.shutdown()
    
    state_info.curr_state = 'MENU'
    
    return state_info


async def displayMenu(state_info):
    
    if state_info.lobbies == None:
        state_info.curr_state = 'QUIT'
        return
    
    # Display lobbies
    state_info.display_lobbies(indexed=True)
    
    # Display options
    state_info.stdscr.addstr('0: host\n')
    state_info.stdscr.addstr('r: refresh\n')
    state_info.stdscr.addstr('q: quit\n')
    
    # Display prompt
    state_info.stdscr.addstr(f'\n> {state_info.input_buffer}')


# Main state machine loop
async def setState(state_info):
    
    # Initial retrieval of lobbies
    await state_info.get_lobbies()
    
    # Main loop
    while state_info.curr_state != 'QUIT':
        
        if state_info.curr_state not in state_info.state_funcs_dict:
            state_info.stdscr.addstr(f'Fatal error: undefined state \'{state_info.curr_state}\'\n')
            state_info.stdscr.refresh()
            break
        
        drawn_state = state_info.curr_state
        
        # Display current state
        state_info.stdscr.clear()
        await state_info.state_funcs_dict[state_info.curr_state][0](state_info)
        state_info.stdscr.refresh()
        
        # If state changed (error)
        if state_info.curr_state != drawn_state:
            continue
        
        # Get input and transition to next state
        state_info = await state_info.state_funcs_dict[state_info.curr_state][1](state_info)


class StateInfo:
    def __init__(self, stdscr):
        self.state_funcs_dict = {'MENU': (displayMenu, menuState), 'HOST': (displayHost, hostState), 'JOIN': (displayJoin, joinState)}
        self.stdscr = stdscr
        self.input_buffer = ''
        
        self.name = os.getlogin()
        self.settings = Settings()
        
        self.curr_state = 'MENU'
        self.lobbies = None
        
        # Client or Host
        self.handle = None
    
    
    async def get_lobbies(self):
        # Try to get catalog within time limit
        try:
            async with asyncio.timeout(self.settings.DELAY):
                response = await self._get_catalog()
        
        except TimeoutError:
            self.lobbies = None
            return
        
        # Parse response body
        self._parse_catalog(response)
    
    
    async def _get_catalog(self):
        http_conn = http.client.HTTPConnection(self.settings.CATALOG_SERVER)
        http_conn.request('GET', '/query.json')
        response = http_conn.getresponse()
        http_conn.close()
        
        return response
    
    
    def _parse_catalog(self, response):
        lobbies = list()
        catalog = json.loads(response.read())
        
        for entry in catalog:
            
            # If the entry dict has the necessary keys
            if all(key in entry for key in ('type', 'lastheardfrom', 'num_clients', 'address', 'port', 'owner')):
                
                # If the entry is an open lobby (correct type, not stale, not full)
                if entry['type'] == self.settings.ENTRY_TYPE and entry['lastheardfrom'] >= time.time_ns() / 1000000000.0 - self.settings.REGISTER_INTERVAL - self.settings.DELAY and entry['num_clients'] < self.settings.MAX_CLIENTS:
                    
                    # Ensure entry is most recent entry of its kind
                    most_recent = True
                    for i, lobby in enumerate(lobbies):
                        if lobby['address'] == entry['address'] and lobby['port'] == entry['port'] and lobby['owner'] == entry['owner']:
                            if lobby['lastheardfrom'] < entry['lastheardfrom']:
                                lobbies[i] = entry
                                most_recent = False
                                break
                    
                    if most_recent:
                        lobbies.append(entry)
        
        # Sort lobbies by most to least recent
        lobbies.sort(key=lambda x: x['lastheardfrom'], reverse=True)
        
        self.lobbies = lobbies
    
    
    def display_lobbies(self, indexed=False):
        for i, lobby in enumerate(self.lobbies, start=1):
            if indexed:
                self.stdscr.addstr(f'{i}: {lobby["owner"]} - {lobby["address"]}:{lobby["port"]} [{lobby["num_clients"]}/{self.settings.MAX_CLIENTS}]\n')
            else:
                self.stdscr.addstr(f'{lobby["owner"]} - {lobby["address"]}:{lobby["port"]} [{lobby["num_clients"]}/{self.settings.MAX_CLIENTS}]\n')


def main(stdscr):
    # Force curses not to do dumb stuff
    curses.use_default_colors()
    
    # Set to non-blocking
    stdscr.nodelay(True)
    
    # Enable normal reading of backspace
    stdscr.keypad(False)
    
    # Initialize state
    state_info = StateInfo(stdscr)
    
    # Run program
    asyncio.run(setState(state_info))
    
    # Give 1 second to read output before it's cleared by curses wrapper
    stdscr.addstr('Closing program...\n')
    stdscr.refresh()
    time.sleep(1)


if __name__ == '__main__':
    stdscr = curses.initscr()
    curses.wrapper(main)
