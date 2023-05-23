#!/usr/bin/env python3
# lobby.py

# To read stdin and write stdout without blocking 
import curses

# To handle connections and messages asynchronously
import asyncio

# time.time_ns() to date messages
import time

# os.getlogin() to get username
import os

# To send and receive data structures via messages
import json

# To get catalog
import http.client

# To get host address and port
import socket


# Host a lobby
async def hostState(state_info):
    
    # Listen for user input
    char = state_info.stdscr.getch()
    while char == -1:
        await asyncio.sleep(0)
        char = state_info.stdscr.getch()
    
    if chr(char) != '\n':
        # Update internal buffer
        async with state_info.stdscr_lock:
            # '\x7f' is backspace, i don't know why
            if chr(char) == '\x7f' and state_info.input_buffer != '':
                state_info.input_buffer = state_info.input_buffer[:-1]
            elif chr(char).isalnum():
                state_info.input_buffer += chr(char)
        
        return state_info
    
    # Parse user input
    await state_info.stdscr_lock.acquire()
    
    choice = state_info.input_buffer
    state_info.input_buffer = ''
    state_info.stdscr.addch('\n')
    state_info.stdscr.refresh()
    
    await state_info.clients_lock.acquire()
    
    # Parse user input
    if not choice.isnumeric() or int(choice) > len(state_info.clients) or choice == '0':
        
        if choice == 'r':
            await state_info.get_lobbies()
            state_info.clients_lock.release()
        
        elif choice == 'd':
            # Kick all clients
            message = str(json.dumps({'command': 'kick'}))
            message_size = len(message.encode()).to_bytes(8, 'big')
            
            clients = [client for client in state_info.clients]
            clients.sort(key=lambda x: x[3])
            
            for client in clients:
                client[2].write(message_size + message.encode())
                await client[2].drain()
                
                # Cancel serving coro
                state_info.clients[client]['task'].cancel()
                # Remove client
                del state_info.clients[client]
            
            state_info.clients_lock.release()
            
            state_info.register()
            await state_info.get_lobbies()
            
            # Return to menu
            state_info.curr_state = 'MENU'
            async with state_info.clients_lock:
                state_info.shutdown_host()
        
        elif choice == 's':
            # TODO: Implement start
            state_info.clients_lock.release()
        
        elif choice == 'q':
            # Kick all clients
            message = str(json.dumps({'command': 'kick'}))
            message_size = len(message.encode()).to_bytes(8, 'big')
            
            clients = [client for client in state_info.clients]
            
            for client in clients:
                client[2].write(message_size + message.encode())
                await client[2].drain()
                
                # Cancel serving coro
                state_info.clients[client]['task'].cancel()
                # Remove client
                del state_info.clients[client]
            
            state_info.clients_lock.release()
            
            state_info.register()
            await state_info.get_lobbies()
            
            state_info.curr_state = 'QUIT'
            async with state_info.clients_lock:
                state_info.shutdown_host()
        
        state_info.stdscr_lock.release()
        
        return state_info
        
    # Kick client
    message = str(json.dumps({'command': 'kick'}))
    message_size = len(message.encode()).to_bytes(8, 'big')
    
    clients = [client for client in state_info.clients]
    clients.sort(key=lambda x: x[3])
    
    clients[int(choice) - 1][2].write(message_size + message.encode())
    await clients[int(choice) - 1][2].drain()
    
    # Cancel serving coro
    state_info.clients[clients[int(choice) - 1]]['task'].cancel()
    # Remove client
    del state_info.clients[clients[int(choice) - 1]]
    
    # Send refresh request to all other clients
    message = str(json.dumps({'command': 'refresh'}))
    message_size = len(message.encode()).to_bytes(8, 'big')
    
    clients.pop(int(choice) - 1)
    for client in clients:
        client[2].write(message_size + message.encode())
        await client[2].drain()
    
    state_info.clients_lock.release()
    
    state_info.register()
    await state_info.get_lobbies()
    
    state_info.stdscr_lock.release()
    
    return state_info


async def displayHost(state_info):
    
    if state_info.lobbies == None:
        state_info.curr_state = 'QUIT'
        # Shutdown host coroutines and clear host state
        async with state_info.clients_lock:
            state_info.shutdown_host()
        return
    
    # Display lobbies (without an index)
    state_info.display_lobbies()
    
    # Display own lobby and kick options
    state_info.stdscr.addch('\n')
    state_info.stdscr.addstr(f'{state_info.name}\n')
    async with state_info.clients_lock:
        clients = [client for client in state_info.clients]
        clients.sort(key=lambda x: x[3])
        client_names = [client[0] for client in clients]
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
    char = state_info.stdscr.getch()
    while char == -1:
        await asyncio.sleep(0)
        if state_info.curr_state == 'MENU': 
            state_info.shutdown_client()
            await state_info.get_lobbies()
            return state_info
        
        char = state_info.stdscr.getch()
    
    if chr(char) != '\n':
        # Update internal buffer
        async with state_info.stdscr_lock:
            # '\x7f' is backspace, i don't know why
            if chr(char) == '\x7f' and state_info.input_buffer != '':
                state_info.input_buffer = state_info.input_buffer[:-1]
            elif chr(char).isalnum():
                state_info.input_buffer += chr(char)
        
        return state_info
    
    await state_info.stdscr_lock.acquire()
    
    choice = state_info.input_buffer
    state_info.input_buffer = ''
    state_info.stdscr.addch('\n')
    state_info.stdscr.refresh()
    
    # Parse user input
    if choice == 'r':
        await state_info.get_lobbies()
        await state_info.get_client_names()
        await asyncio.sleep(1)
    
    elif choice == 'l':
        state_info.curr_state = 'MENU'
        
        # Send leave message to host
        message = str(json.dumps({'command': 'leave'}))
        message_size = len(message.encode()).to_bytes(8, 'big')
        state_info.writer.write(message_size + message.encode())
        await state_info.writer.drain()
        
        state_info.shutdown_client()
        
        await state_info.get_lobbies()
    
    elif choice == 'q':
        state_info.curr_state = 'QUIT'
        
        # Send leave message to host
        message = str(json.dumps({'command': 'leave'}))
        message_size = len(message.encode()).to_bytes(8, 'big')
        state_info.writer.write(message_size + message.encode())
        await state_info.writer.drain()
        
        state_info.shutdown_client()
    
    state_info.stdscr_lock.release()
    
    return state_info


async def displayJoin(state_info):
    
    # Check lobbies
    if state_info.lobbies == None:
        state_info.curr_state = 'QUIT'
        await state_info.shutdown_client()
        return
    
    # Check client names
    if state_info.client_names == None:
        state_info.curr_state = 'MENU'
        state_info.shutdown_client()
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
    char = state_info.stdscr.getch()
    while char == -1:
        await asyncio.sleep(0)
        char = state_info.stdscr.getch()
    
    if chr(char) != '\n':
        # Update internal buffer
        async with state_info.stdscr_lock:
            # '\x7f' is backspace, i don't know why
            if chr(char) == '\x7f' and state_info.input_buffer != '':
                state_info.input_buffer = state_info.input_buffer[:-1]
            elif chr(char).isalnum():
                state_info.input_buffer += chr(char)
        
        return state_info
    
    # Parse user input
    await state_info.stdscr_lock.acquire()
    
    choice = state_info.input_buffer
    state_info.input_buffer = ''
    state_info.stdscr.addch('\n')
    state_info.stdscr.refresh()
    
    if not choice.isnumeric() or int(choice) > len(state_info.lobbies):
        
        if choice == 'r':
            await state_info.get_lobbies()
            
        elif choice == 'q':
            state_info.curr_state = 'QUIT'
        
        state_info.stdscr_lock.release()
        
        return state_info
    
    state_info.stdscr_lock.release()
    
    if choice == '0':
        # Create server object
        state_info.server = await asyncio.start_server(state_info.handle_client, host=socket.gethostname(), backlog=state_info.settings.MAX_CLIENTS)
        
        # Set host attributes
        state_info.addr = state_info.server.sockets[0].getsockname()[0]
        state_info.port = state_info.server.sockets[0].getsockname()[1]
        
        await state_info.stdscr_lock.acquire()
        await state_info.clients_lock.acquire()
        
        # Try to register with catalog server
        if state_info.register() == 0:
            state_info.stdscr_lock.release()
            state_info.clients_lock.release()
            
            state_info.curr_state = 'QUIT'
            
            # Shutdown host coroutines and clear host state
            async with state_info.clients_lock:
                state_info.shutdown_host()
            
            return state_info
        
        state_info.stdscr_lock.release()
        state_info.clients_lock.release()
        
        # Register every REGISTER_INTERVAL seconds
        state_info.register_task = asyncio.create_task(state_info.register_interval())
        
        # Check all pings every PING_INTERVAL seconds
        state_info.check_ping_task = asyncio.create_task(state_info.check_pings())
        
        # Get lobbies (should see self in list of lobbies)
        await state_info.get_lobbies()
        if state_info.lobbies == None:
            state_info.curr_state = 'QUIT'
            async with state_info.clients_lock:
                state_info.shutdown_host()
            return state_info
        
        state_info.curr_state = 'HOST'
        
        return state_info
    
    # Save lobby choice
    state_info.host_name = state_info.lobbies[int(choice) - 1]['owner']
    state_info.host_addr = state_info.lobbies[int(choice) - 1]['address']
    state_info.host_port = state_info.lobbies[int(choice) - 1]['port']
    
    # Try to connect to chosen lobby
    state_info.reader, state_info.writer = await asyncio.open_connection(host=state_info.host_addr, port=state_info.host_port)
    
    # Send name to host
    message = str(json.dumps({'command': 'join', 'name': state_info.name}))
    message_size = len(message.encode()).to_bytes(8, 'big')
    state_info.writer.write(message_size + message.encode())
    await state_info.writer.drain()
    
    response = await state_info.get_message()
    
    # Parse response
    if all(key in response for key in ('command', 'status')):
        if response['command'] == 'join' and response['status'] == 'success':
            
            async with state_info.stdscr_lock:
                state_info.stdscr.addstr(f'LOBBIES START\n')
                state_info.stdscr.refresh()
            
            #time.sleep(2)
            
            # Refresh lobby
            await state_info.get_lobbies()
            if state_info.lobbies == None:
                state_info.curr_state = 'QUIT'
                state_info.shutdown_client()
                return state_info
            
            async with state_info.stdscr_lock:
                state_info.stdscr.addstr(f'CLIENT NAMES START\n')
                state_info.stdscr.refresh()
            
            #time.sleep(2)
            # Listen to host for refresh requests or kicks
            state_info.listen_task = asyncio.create_task(state_info.listen_to_host())
            
            # Get client names
            await state_info.get_client_names()
            await asyncio.sleep(1)
            if state_info.client_names == None:
                # Error joining lobby
                state_info.curr_state = 'MENU'
                state_info.shutdown_client()
                return state_info
            
            async with state_info.stdscr_lock:
                state_info.stdscr.addstr(f'DONE\n')
                state_info.stdscr.refresh()
            
            #time.sleep(2)
            
            # Register every PING_INTERVAL seconds
            state_info.ping_task = asyncio.create_task(state_info.ping_interval())
            
            state_info.curr_state = 'JOIN'
            return state_info
    
    # Error joining lobby
    state_info.curr_state = 'MENU'
    state_info.shutdown_client()
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
    
    async with state_info.stdscr_lock:
        await state_info.get_lobbies()
        state_info.stdscr.refresh()
    
    while state_info.curr_state != 'QUIT':
        if state_info.curr_state not in state_info.state_funcs_dict:
            async with state_info.stdscr_lock:
                state_info.stdscr.addstr(f'Fatal error: undefined state \'{state_info.curr_state}\'\n')
                state_info.stdscr.refresh()
            break
        
        state = state_info.curr_state
        
        # Display current state
        async with state_info.stdscr_lock:
            state_info.stdscr.clear()
            await state_info.state_funcs_dict[state_info.curr_state][0](state_info)
            state_info.stdscr.refresh()
        
        # If state changed
        if state_info.curr_state != state:
            continue
        
        # Get input and transition to next state
        state_info = await state_info.state_funcs_dict[state_info.curr_state][1](state_info)


class Settings:
    def __init__(self):
        self.ENTRY_TYPE = 'Tong-its'
        self.CATALOG_SERVER = 'catalog.cse.nd.edu:9097'
        self.REGISTER_INTERVAL = 30
        self.PING_INTERVAL = 1
        self.DELAY = 1
        self.MIN_CLIENTS = 2
        self.MAX_CLIENTS = 2


class StateInfo:
    def __init__(self, stdscr):
        # Dict of state names mapped to their respective state functions
        self.state_funcs_dict = {'MENU': (displayMenu, menuState), 'HOST': (displayHost, hostState), 'JOIN': (displayJoin, joinState)}
        
        # Config
        # Lock for stdscr, input_buffer, and lobbies 8|
        self.stdscr_lock = asyncio.Lock()
        self.stdscr = stdscr
        self.input_buffer = ''
        self.settings = Settings()
        
        # Player
        self.curr_state = 'MENU'
        self.name = os.getlogin()
        self.lobbies = None
        
        # Host
        self.server = None
        self.addr = None
        self.port = None
        self.register_task = None
        self.check_ping_task = None
        self.clients_lock = asyncio.Lock()
        self.clients = dict()
        
        # Client
        self.host_name = None
        self.host_addr = None
        self.host_port = None
        self.client_names = None
        self.listen_task = None
        self.ping_task = None
        self.reader = None
        self.writer = None
    
    
    # Requires stdscr_lock!
    async def get_lobbies(self):
        # Try to get catalog within time limit
        try:
            async with asyncio.timeout(self.settings.DELAY):
                response = await self._get_catalog()
        
        except TimeoutError:
            self._get_catalog_fail()
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
                
                # If the entry is an open lobby (correct type, not stale, not full) TODO: I changed the num_clients so it shows full lobbies :P
                if entry['type'] == self.settings.ENTRY_TYPE and entry['lastheardfrom'] >= time.time_ns() / 1000000000.0 - self.settings.REGISTER_INTERVAL - self.settings.DELAY and entry['num_clients'] <= self.settings.MAX_CLIENTS:
                    
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
    
    
    def _get_catalog_fail(self):
        self.stdscr.addstr('Fatal error: failed to get catalog from catalog server\n')
        self.stdscr.refresh()
    
    
    def display_lobbies(self, indexed=False):
        # Display lobbies
        for i, lobby in enumerate(self.lobbies, start=1):
            if indexed:
                self.stdscr.addstr(f'{i}: {lobby["owner"]} - {lobby["address"]}:{lobby["port"]} [{lobby["num_clients"]}/{self.settings.MAX_CLIENTS}]\n')
            else:
                self.stdscr.addstr(f'{lobby["owner"]} - {lobby["address"]}:{lobby["port"]} [{lobby["num_clients"]}/{self.settings.MAX_CLIENTS}]\n')
    
    
    async def get_message(self):
        try:
            async with asyncio.timeout(self.settings.DELAY):
                # Get response
                response_size = int.from_bytes((await self.reader.readexactly(8)), 'big')
                return json.loads((await self.reader.readexactly(response_size)).decode())
        
        except TimeoutError:
            response = dict()
        
        except:
            response = dict()
        
        return response
    
    
    # Ping host every PING_INTERVAL seconds
    async def ping_interval(self):
        while True:
            await asyncio.sleep(self.settings.PING_INTERVAL)
            # Ping host
            message = str(json.dumps({'command': 'ping'}))
            message_size = len(message.encode()).to_bytes(8, 'big')
            self.writer.write(message_size + message.encode())
            await self.writer.drain()
    
    
    # Check clients' last pings every PING_INTERVAL seconds
    async def check_pings(self):
        while True:
            await asyncio.sleep(self.settings.PING_INTERVAL)
            
            await self.stdscr_lock.acquire()
            
            async with self.clients_lock:
                num_clients = len(self.clients)
                
                # Check all pings
                clients = [client for client in self.clients]
                for client in clients:
                    if self.clients[client]['lastping'] < time.time_ns() / 1000000000.0 - self.settings.PING_INTERVAL - self.settings.DELAY:
                        # Kick client
                        message = str(json.dumps({'command': 'kick'}))
                        message_size = len(message.encode()).to_bytes(8, 'big')
                        client[2].write(message_size + message.encode())
                        await client[2].drain()
                        
                        # Cancel serving coro
                        self.clients[client]['task'].cancel()
                        # Remove client
                        self.clients.pop(client)
                
                # If number of clients changed (if some were kicked)
                if len(self.clients) != num_clients:
                    # Register
                    self.register()
                    
                    # Refresh display
                    await self.get_lobbies()
                    self.stdscr.clear()
                    self.clients_lock.release()
                    await self.state_funcs_dict['HOST'][0](self)
                    await self.clients_lock.acquire()
                    self.stdscr.refresh()
            
            self.stdscr_lock.release()
    
    
    # Requires self.clients_lock!
    # Try to register with catalog server
    def register(self):
        try:
            return socket.socket(socket.AF_INET, socket.SOCK_DGRAM).sendto(str(json.dumps({'type': self.settings.ENTRY_TYPE, 'owner': self.name, 'port': self.port, 'num_clients': len(self.clients)})).encode(), (self.settings.CATALOG_SERVER[:-5], int(self.settings.CATALOG_SERVER[-4:])))
        
        except asyncio.CancelledError:
            return 0
            
        except:
            self._register_fail()
            return 0
    
    
    # Register with catalog server every REGISTER_INTERVAL seconds
    async def register_interval(self):
        while True:
            await asyncio.sleep(self.settings.REGISTER_INTERVAL)
            async with self.clients_lock:
                if self.register() == 0:
                    return
    
    
    # Output for consistent error logging
    def _register_fail(self):
        self.stdscr.addstr('Fatal error: failed to register with catalog server\n')
        self.stdscr.refresh()
    
    
    async def listen_to_host(self):
        
        while True:
            response_size = int.from_bytes((await self.reader.readexactly(8)), 'big')
            response = json.loads((await self.reader.readexactly(response_size)).decode())
            
            if 'command' in response and response['command'] == 'refresh':
                async with self.stdscr_lock:
                    await self.get_lobbies()
                    # Request client names
                    message = str(json.dumps({'command': 'get_client_names'}))
                    message_size = len(message.encode()).to_bytes(8, 'big')
                    self.writer.write(message_size + message.encode())
                    await self.writer.drain()
                    response_size = int.from_bytes((await self.reader.readexactly(8)), 'big')
                    response = json.loads((await self.reader.readexactly(response_size)).decode())
                    self.client_names = response['client_names']
                    
                    self.stdscr.clear()
                    await self.state_funcs_dict['JOIN'][0](self)
                    self.stdscr.refresh()
            
            elif 'command' in response and response['command'] == 'kick':
                async with self.stdscr_lock:
                    self.curr_state = 'MENU'
                    return
            elif 'command' in response and response['command'] == 'get_client_names':
                if response['command'] == 'get_client_names' and response['status'] == 'success':
                    self.client_names = response['client_names']
                else:
                    self.client_names = None
    
    # Listen to messages from client
    async def _serve_client(self, client):
        
        while True:
            
            # 'client' is a tuple with 'name', 'reader', 'writer', and 'join_time'
            
            # Get message
            message_size = int.from_bytes((await client[1].readexactly(8)), 'big')
            message = json.loads((await client[1].readexactly(message_size)).decode())
            
            # Parse message
            if 'command' in message:
                
                # Perhaps a retried message that got delayed - probably safe to just ignore it
                if message['command'] == 'join':
                    pass
                
                elif message['command'] == 'get_client_names':
                    
                    async with self.clients_lock:
                        clients = [c for c in self.clients]
                        clients.sort(key=lambda x: x[3])
                    
                    client_names = [c[0] for c in clients]
                    
                    # Send response
                    response = str(json.dumps({'command': 'get_client_names', 'status': 'success', 'client_names': client_names}))
                    response_size = len(response.encode()).to_bytes(8, 'big')
                    client[2].write(response_size + response.encode())
                    await client[2].drain()
                
                elif message['command'] == 'leave':
                    
                    async with self.clients_lock:
                        del self.clients[client]
                        
                        # Register with catalog to send update
                        self.register()
                        
                        # Send refresh command
                        response = str(json.dumps({'command': 'refresh'}))
                        response_size = len(response.encode()).to_bytes(8, 'big')
                        for client in self.clients:
                            client[2].write(response_size + response.encode())
                            await client[2].drain()
                        
                    # Terminate
                    async with self.stdscr_lock:
                        await self.get_lobbies()
                        self.stdscr.clear()
                        await self.state_funcs_dict['HOST'][0](self)
                        self.stdscr.refresh()
                    
                    return
                
                elif message['command'] == 'ping':
                    async with self.clients_lock:
                        self.clients[client]['lastping'] = time.time_ns() / 1000000000.0
    
    
    # Handle incoming connection attempt from client
    async def handle_client(self, reader, writer):
        
        await self.stdscr_lock.acquire()
        
        await self.clients_lock.acquire()
        
        # Get message
        message_size = int.from_bytes((await reader.readexactly(8)), 'big')
        message = json.loads((await reader.readexactly(message_size)).decode())
        
        # Parse message
        if all(key in message for key in ('command', 'name')) and message['command'] == 'join' and len(self.clients) < self.settings.MAX_CLIENTS:
            
            join_time = time.time_ns() / 1000000000.0
            
            # Accept client
            client = (message['name'], reader, writer, join_time)
            
            # Serve client asynchronously from here on out
            self.clients[client] = {'task': asyncio.create_task(self._serve_client(client)), 'lastping': join_time}
            
            # Try to register with catalog server
            if self.register() == 0:
                self.curr_state = 'QUIT'
                
                # Shutdown host coroutines and clear host state
                self.shutdown_host()
                
                self.stdscr_lock.release()
                self.clients_lock.release()
                
                return
            
            # Send response
            response = str(json.dumps({'command': 'join', 'status': 'success'}))
            response_size = len(response.encode()).to_bytes(8, 'big')
            writer.write(response_size + response.encode())
            await writer.drain()
            
            self.stdscr_lock.release()
            self.clients_lock.release()
            
            # Send refresh request to all clients
            async with self.clients_lock:
                message = str(json.dumps({'command': 'refresh'}))
                message_size = len(message.encode()).to_bytes(8, 'big')
                
                for c in self.clients:
                    c[2].write(message_size + message.encode())
                    await c[2].drain()
            
            # Refresh display
            async with self.stdscr_lock:
                await self.get_lobbies()
                self.stdscr.clear()
                await self.state_funcs_dict[self.curr_state][0](self)
                self.stdscr.refresh()
            
            return
        
        else:
            
            # Send response
            response = str(json.dumps({'command': 'join', 'status': 'failure'}))
            response_size = len(response.encode()).to_bytes(8, 'big')
            writer.write(response_size + response.encode())
            await writer.drain()
            
            # Close connection
            writer.close()
            await writer.wait_closed()
        
        self.stdscr_lock.release()
        self.clients_lock.release()
    
    
    async def get_client_names(self):
        # Request client names
        message = str(json.dumps({'command': 'get_client_names'}))
        message_size = len(message.encode()).to_bytes(8, 'big')
        self.writer.write(message_size + message.encode())
        await self.writer.drain()
        
        # Get response
        #response = await self.get_message()
        '''
        # Parse response
        if all(key in response for key in ('command', 'status', 'client_names')):
            if response['command'] == 'get_client_names' and response['status'] == 'success':
                self.client_names = response['client_names']
                return
        
        self.client_names = None
        '''
    
    
    # Requires clients_lock!
    def shutdown_host(self):
        for client in self.clients:
            self.clients[client]['task'].cancel()
        
        if self.register_task != None:
            self.register_task.cancel()
            self.register_task = None
        
        if self.check_ping_task != None:
            self.check_ping_task.cancel()
            self.check_ping_task = None
        
        self.server = None
        self.addr = None
        self.port = None
        
        self.clients = dict()
    
    
    def shutdown_client(self):
        self.host_name = None
        self.host_addr = None
        self.host_port = None
        self.client_names = None
        
        if self.listen_task != None:
            self.listen_task.cancel()
            self.listen_task = None
        
        if self.ping_task != None:
            self.ping_task.cancel()
            self.ping_task = None
        
        self.reader = None
        self.writer = None


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
