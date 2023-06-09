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

# Predefined constants and helper functions
from config import Settings, get_message, send_message

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
            return state_info
            
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
            state_info.handle = None
            
            # Refresh lobbies after shutdown
            await state_info.get_lobbies()
            
            state_info.curr_state = 'MENU'
        
        elif choice == 's':
            async with state_info.handle.clients_lock:
                
                # Send start message to all clients
                num_clients = len(state_info.handle.clients)
                for client in state_info.handle.clients:
                    if (await send_message(client[1], {'command': 'start'}) == 0):
                        # Kick client
                        await send_message(client[1], {'command': 'kick'})
                        
                        # Trigger shutdown for client handler
                        state_info.handle.clients[client]['shutdown'].set()
                
                # If all start messages sent successfully
                if len(state_info.handle.clients) == num_clients:
                    state_info.handle.register_task.cancel()
                    state_info.handle.purge_task.cancel()
                    
                    state_info.handle.server.close()
                    await state_info.handle.server.wait_closed()
                    
                    state_info.curr_state = 'START'
        
        elif choice == 'q':
            # Shutdown host
            await state_info.handle.shutdown()
            state_info.handle = None
            
            state_info.curr_state = 'QUIT'
        
        return state_info
        
    # Kick client
    clients_copy = [client for client in state_info.handle.clients]
    clients_copy.sort(key=lambda x: state_info.handle.clients[x]['join_time'])
    client = clients_copy[int(choice) - 1]
    
    # Send kick
    await send_message(client[1], {'command': 'kick'})
    
    # Trigger shutdown in client handler
    state_info.handle.clients[client]['shutdown'].set()
    
    state_info.handle.clients_lock.release()
    
    return state_info


async def displayHost(state_info):
    
    if state_info.lobbies == None:
        state_info.curr_state = 'QUIT'
        # Shutdown host
        await state_info.handle.shutdown()
        state_info.handle = None
        return
    
    # Display lobbies (without an index)
    state_info.display_lobbies()
    
    # Display own lobby and kick options
    state_info.stdscr.addch('\n')
    state_info.stdscr.addstr(f'{state_info.name}\n')
    async with state_info.handle.clients_lock:
        clients_copy = [state_info.handle.clients[client] for client in state_info.handle.clients]
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
        
        # Check if client has shutdown
        if state_info.handle.shutdown_flag.is_set():
            await state_info.handle.shutdown()
            state_info.handle = None
            await state_info.get_lobbies()
            state_info.curr_state = 'MENU'
            return state_info
        
        # Refresh if needed
        if state_info.handle.refresh_flag.is_set():
            state_info.handle.refresh_flag.clear()
            await state_info.get_lobbies()
            return state_info
            
        # Check if game is starting
        if state_info.handle.start_flag.is_set():
            state_info.handle.ping_task.cancel()
            state_info.handle.listen_task.cancel()
            state_info.curr_state = 'START'
            return state_info
        
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
        if (await send_message(state_info.handle.writer, {'command': 'get_client_names'})) == 0:
            # Shutdown client
            await state_info.handle.shutdown()
            state_info.handle = None
            
            state_info.curr_state = 'MENU'
    
    elif choice == 'l':
        # Send leave message to host
        await send_message(state_info.handle.writer, {'command': 'leave'})
        
        # Shutdown client
        await state_info.handle.shutdown()
        state_info.handle = None
        
        # Refresh lobbies after shutdown
        await state_info.get_lobbies()
        
        state_info.curr_state = 'MENU'
    
    elif choice == 'q':
        # Send leave message to host
        await send_message(state_info.handle.writer, {'command': 'leave'})
        
        # Shutdown client
        await state_info.handle.shutdown()
        state_info.handle = None
        
        state_info.curr_state = 'QUIT'
    
    return state_info


async def displayJoin(state_info):
    
    # Check lobbies
    if state_info.lobbies == None:
        # Shutdown client
        await state_info.handle.shutdown()
        state_info.handle = None
        state_info.curr_state = 'QUIT'
        return
    
    # Check client names
    async with asyncio.timeout(Settings().DELAY):
        try:
            while state_info.handle.client_names == None:
                await asyncio.sleep(0)
        
        except TimeoutError:
            # Shutdown client
            await state_info.handle.shutdown()
            state_info.handle = None
            state_info.curr_state = 'MENU'
            return
    
    # Display lobbies
    state_info.display_lobbies()
    
    # Display host name
    state_info.stdscr.addch('\n')
    state_info.stdscr.addstr(f'{state_info.handle.host_name}\n')
    
    # Display client names
    for client_name in state_info.handle.client_names:
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
        state_info.handle.server = await asyncio.start_server(state_info.handle.handle_client, host=socket.gethostname(), backlog=Settings().MAX_CLIENTS)
        
        # Save port for registration and shutdown
        state_info.handle.port = state_info.handle.server.sockets[0].getsockname()[1]
        
        # Try to register with catalog server
        state_info.handle.register()
        
        # Register every REGISTER_INTERVAL seconds
        state_info.handle.register_task = asyncio.create_task(state_info.handle.register_coro())
        
        # Check all pings every PING_INTERVAL seconds
        state_info.handle.purge_task = asyncio.create_task(state_info.handle.purge_coro())
        
        # Get lobbies (should see self in list of lobbies)
        state_info.handle.refresh_flag.clear()
        await state_info.get_lobbies()
        
        state_info.curr_state = 'HOST'
        
        return state_info
    
    state_info.handle = Client()
    
    # Save lobby choice
    state_info.handle.host_name = state_info.lobbies[int(choice) - 1]['owner']
    
    # Try to connect to chosen lobby
    try:
        state_info.handle.reader, state_info.handle.writer = await asyncio.open_connection(state_info.lobbies[int(choice) - 1]['address'], state_info.lobbies[int(choice) - 1]['port'])
    
    except ConnectionRefusedError:
        # Reset handle
        state_info.handle = None
        
        # Refresh lobbies
        await state_info.get_lobbies()
        
        # Return to MENU
        return state_info
    
    # Send name to host
    if (await send_message(state_info.handle.writer, {'command': 'join', 'name': state_info.name}) == 0):
        # Error joining lobby
        await state_info.handle.shutdown()
        state_info.handle = None
        
        # Refresh lobbies
        await state_info.get_lobbies()
        
        # Return to MENU
        return state_info
    
    # Get response
    response = await get_message(state_info.handle.reader)
    
    # Parse response
    if response['status'] == 'success':
        
        # Listen to host for refresh requests or kicks
        state_info.handle.listen_task = asyncio.create_task(state_info.handle.listen_coro())
        
        # Register every PING_INTERVAL seconds
        state_info.handle.ping_task = asyncio.create_task(state_info.handle.ping_coro())
        
        state_info.curr_state = 'JOIN'
        
        return state_info
    
    # Error joining lobby
    await state_info.handle.shutdown()
    state_info.handle = None
    
    # Refresh lobbies
    await state_info.get_lobbies()
    
    # Return to MENU
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
    while all(state_info.curr_state != state for state in ('QUIT', 'START')):
        
        # Check if state is valid
        if state_info.curr_state not in state_info.state_funcs_dict:
            state_info.stdscr.addstr(f'Fatal error: undefined state \'{state_info.curr_state}\'\n')
            state_info.stdscr.refresh()
            break
        
        # Save displayed state
        drawn_state = state_info.curr_state
        
        # Display current state
        state_info.stdscr.clear()
        await state_info.state_funcs_dict[state_info.curr_state][0](state_info)
        state_info.stdscr.refresh()
        
        # Evaluate whether state changed during displaying
        if state_info.curr_state != drawn_state:
            continue
        
        # Get input and transition to next state
        state_info = await state_info.state_funcs_dict[state_info.curr_state][1](state_info)
    
    if state_info.curr_state == 'START':
        if type(state_info.handle) is Host:
            async with state_info.handle.clients_lock:
                clients = list()
                for client in state_info.handle.clients:
                    clients.append((client[0], client[1], state_info.handle.clients[client]['name']))
                
                clients.sort(key=lambda x: state_info.handle.clients[(x[0], x[1])]['join_time'])
            
            return clients
        
        elif type(state_info.handle) is Client:
            host = (state_info.handle.reader, state_info.handle.writer, state_info.handle.host_name)
            
            return host


class StateInfo:
    def __init__(self, stdscr):
        self.state_funcs_dict = {'MENU': (displayMenu, menuState), 'HOST': (displayHost, hostState), 'JOIN': (displayJoin, joinState)}
        self.stdscr = stdscr
        self.input_buffer = ''
        
        self.name = os.getlogin()
        
        self.curr_state = 'MENU'
        self.lobbies = None
        
        # Client or Host
        self.handle = None
    
    
    async def get_lobbies(self):
        # Try to get catalog within time limit
        try:
            async with asyncio.timeout(Settings().DELAY):
                response = await self._get_catalog()
        
        except TimeoutError:
            self.lobbies = None
            return
        
        # Parse response body
        self._parse_catalog(response)
    
    
    async def _get_catalog(self):
        http_conn = http.client.HTTPConnection(Settings().CATALOG_SERVER)
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
                if entry['type'] == Settings().ENTRY_TYPE and entry['lastheardfrom'] >= time.time_ns() / 1000000000.0 - Settings().REGISTER_INTERVAL - Settings().DELAY and entry['num_clients'] < Settings().MAX_CLIENTS:
                    
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
                self.stdscr.addstr(f'{i}: {lobby["owner"]} - {lobby["address"]}:{lobby["port"]} [{lobby["num_clients"]}/{Settings().MAX_CLIENTS}]\n')
            else:
                self.stdscr.addstr(f'{lobby["owner"]} - {lobby["address"]}:{lobby["port"]} [{lobby["num_clients"]}/{Settings().MAX_CLIENTS}]\n')


async def start_lobby(stdscr):
    # Force curses not to do dumb stuff
    curses.use_default_colors()
    
    # Set to non-blocking
    stdscr.nodelay(True)
    
    # Enable normal reading of backspace
    stdscr.keypad(False)
    
    # Initialize state
    state_info = StateInfo(stdscr)
    
    # Run program
    return await setState(state_info)


async def main():
    stdscr = curses.initscr()
    return curses.wrapper(start_lobby)
