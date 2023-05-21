#!/usr/bin/env python3
# lobby.py

# To encode strings with one of the system's available encodings, for curses
import locale

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
    
    # Parse user input
    if not choice.isnumeric() or int(choice) > len(lobbies) or choice == '0':
        
        if choice == 'r':
            await state_info.get_lobbies()
        
        elif choice == 'd':
            # TODO: Implement disband
            pass
        
        elif choice == 's':
            # TODO: Implement start
            pass
        
        elif choice == 'q':
            state_info.curr_state = 'QUIT'
            await state_info.shutdown_host()
        
        state_info.stdscr_lock.release()
        
        return state_info
        
    state_info.stdscr_lock.release()
    
    # TODO: Implement kick
    #
    
    return state_info


async def displayHost(state_info):
    
    if state_info.lobbies == None:
        state_info.curr_state = 'QUIT'
        # Shutdown host coroutines and clear host state
        await state_info.shutdown_host()
        return
    
    # Display lobbies (without an index)
    state_info.display_lobbies()
    
    # Display own lobby and kick options
    state_info.stdscr.addch('\n')
    state_info.stdscr.addstr(f'{state_info.name}\n')
    async with state_info.clients_lock:
        for i, client in enumerate(state_info.clients):
            state_info.stdscr.addstr(f'{i}: {client[0]}\n')
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
    
    elif choice == 'l':
        state_info.curr_state = 'MENU'
        # TODO: Implement leave - need to send message to host
        #
        await state_info.shutdown_client()
    
    elif choice == 'q':
        state_info.curr_state = 'QUIT'
        # TODO: Implement quit - need to send message to host
        #
        await state_info.shutdown_client()
    
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
        await state_info.shutdown_client()
        return
    
    # Display lobbies
    state_info.display_lobbies()
    
    # Display host name
    state_info.stdscr.addch('\n')
    state_info.stdscr.addstr(f'{self.host_name}\n')
    
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
            await state_info.shutdown_host()
            
            return state_info
        
        state_info.stdscr_lock.release()
        state_info.clients_lock.release()
        
        # Register every REGISTER_INTERVAL seconds
        state_info.register_task = asyncio.create_task(state_info.register_interval())
        
        # Get lobbies (should see self in list of lobbies)
        await state_info.get_lobbies()
        if state_info.lobbies == None:
            state_info.curr_state = 'QUIT'
            await state_info.shutdown_host()
            return state_info
        
        state_info.curr_state = 'HOST'
        return state_info
    
    # Save lobby choice
    state_info.host_name = state_info.lobbies[int(choice) - 1]['owner']
    state_info.host_addr = state_info.lobbies[int(choice) - 1]['address']
    state_info.host_port = state_info.lobbies[int(choice) - 1]['port']
    
    # Try to connect to chosen lobby
    state_info.reader, state_info.writer = await asyncio.open_connection(state_info.host_addr, state_info.host_port)
    
    # Send name to host
    message = str(json.dumps({'command': 'join', 'name': state_info.name}))
    message_size = len(message.encode(locale.getpreferredencoding())).to_bytes(8, 'big')
    state_info.writer.write(message_size + message.encode(locale.getpreferredencoding()))
    await state_info.writer.drain()
    
    # Get response
    response_size = int.from_bytes((await state_info.reader.readexactly(8)), 'big')
    response = json.loads((await state_info.reader.readexactly(response_size)).decode())
    
    # Parse response
    if all(key in response for key in ('command', 'status')):
        if response['command'] == 'join' and response['status'] == 'success':
            
            # Get client names
            await state_info.get_client_names()
            if state_info.client_names == None:
                # Error joining lobby
                state_info.curr_state = 'MENU'
                await state_info.shutdown_client()
                return state_info
            
            # Register every PING_INTERVAL seconds
            state_info.ping_task = asyncio.create_task(state_info.ping_interval())
            
            state_info.curr_state = 'JOIN'
            return state_info
    
    # Error joining lobby
    state_info.curr_state = 'MENU'
    await state_info.shutdown_client()
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
        self.REGISTER_INTERVAL = 60
        self.PING_INTERVAL = 5
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
        self.clients_lock = asyncio.Lock()
        self.clients = list()
        
        # Client
        self.host_name = None
        self.host_addr = None
        self.host_port = None
        self.client_names = None
        self.ping_task = None
        self.reader = None
        self.writer = None
    
    
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
                
                # If the entry is an open lobby (correct type, not stale, not full)
                if entry['type'] == self.settings.ENTRY_TYPE and entry['lastheardfrom'] >= time.time_ns() / 1000000000.0 - self.settings.REGISTER_INTERVAL and entry['num_clients'] < self.settings.MAX_CLIENTS:
                    
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
    
    
    def display_lobbies(self, indexed=False):
        # Display lobbies
        for i, lobby in enumerate(self.lobbies, start=1):
            if indexed:
                self.stdscr.addstr(f'{i}: {lobby["owner"]} - {lobby["address"]}:{lobby["port"]} [{lobby["num_clients"]}/{self.settings.MAX_CLIENTS}]\n')
            else:
                self.stdscr.addstr(f'{lobby["owner"]} - {lobby["address"]}:{lobby["port"]} [{lobby["num_clients"]}/{self.settings.MAX_CLIENTS}]\n')
    
    
    # Ping host every PING_INTERVAL seconds
    async def ping_interval(self):
        while True:
            await asyncio.sleep(self.settings.PING_INTERVAL)
            # Ping host
            message = str(json.dumps({'command': 'ping'}))
            message_size = len(message.encode(locale.getpreferredencoding())).to_bytes(8, 'big')
            self.writer.write(message_size + message.encode(locale.getpreferredencoding()))
            await self.writer.drain()
    
    
    # Requires self.clients_lock!
    # Try to register with catalog server
    def register(self):
        try:
            return socket.socket(socket.AF_INET, socket.SOCK_DGRAM).sendto(str(json.dumps({'type': self.settings.ENTRY_TYPE, 'owner': self.name, 'port': self.port, 'num_clients': len(self.clients)})).encode(locale.getpreferredencoding()), (self.settings.CATALOG_SERVER[:-5], int(self.settings.CATALOG_SERVER[-4:])))
        
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
                self.register()
    
    
    # Output for consistent error logging
    def _register_fail(self):
        self.stdscr.addstr('Fatal error: failed to register with catalog server\n')
    
    
    # Listen to messages from client
    async def _serve_client(self, i):
        
        while True:
            # Make sure to keep reader operations outside of lock so you don't hold onto the lock for so long
            # TODO: I'm pretty sure this violates the lock tho
            async with self.clients_lock:
                reader = self.clients[i][1]
            
            # Get message
            message_size = int.from_bytes((await reader.readexactly(8)), 'big')
            message = json.loads((await reader.readexactly(message_size)).decode())
            
            # Parse message
            if 'command' in message:
                
                # Perhaps a retried message that got delayed - probably safe to just ignore it
                if message['command'] == 'join':
                    pass
                
                elif message['command'] == 'get_client_names':
                    
                    # TODO: I'm pretty sure this violates the lock
                    async with self.clients_lock:
                        writer = self.clients[i][2]
                        client_names = [client[0] for client in self.clients]
                    
                    # Send response
                    response = str(json.dumps({'command': 'get_client_names', 'status': 'success', 'client_names': client_names}))
                    response_size = len(response.encode(locale.getpreferredencoding())).to_bytes(8, 'big')
                    writer.write(response_size + response.encode(locale.getpreferredencoding()))
                    await writer.drain()
                
                elif message['command'] == 'leave':
                    # TODO: Implement removal of client
                    pass
                
                elif message['command'] == 'ping':
                    # TODO: Implement ping
                    pass
    
    
    # Handle incoming connection attempt from client
    async def handle_client(self, reader, writer):
        
        state_info.stdscr.addstr(state_info.server)
        state_info.stdscr.refresh()
        
        await self.clients_lock.acquire()
        
        # Get message
        message_size = int.from_bytes((await reader.readexactly(8)), 'big')
        message = json.loads((await reader.readexactly(message_size)).decode())
        
        # Parse message
        if all(key in message for key in ('command', 'name')) and message['command'] == 'join' and len(self.clients) < self.settings.MAX_CLIENTS:
            
            # Accept client
            self.clients.append([message['name'], reader, writer])
            
            # Try to register with catalog server
            if self.register() == 0:
                self.clients_lock.release()
                
                self.curr_state = 'QUIT'
                
                # Shutdown host coroutines and clear host state
                await self.shutdown_host()
                
                return
            
            # Send response
            response = str(json.dumps({'command': 'join', 'status': 'success'}))
            response_size = len(response.encode(locale.getpreferredencoding())).to_bytes(8, 'big')
            writer.write(response_size + response.encode(locale.getpreferredencoding()))
            await writer.drain()
            
            # Refresh display
            # TODO: Seems sus if the state changes right before this displayHost function gets called
            #self.state_funcs_dict[self.curr_state][0](self)
            
            # Serve client asynchronously from here on out
            self.clients[-1].append(asyncio.create_task(self._serve_client(len(self.clients) - 1)))
        
        else:
            
            # Send response
            response = str(json.dumps({'command': 'join', 'status': 'failure'}))
            response_size = len(response.encode(locale.getpreferredencoding())).to_bytes(8, 'big')
            writer.write(response_size + response.encode(locale.getpreferredencoding()))
            await writer.drain()
            
            # Close connection
            writer.close()
            await writer.wait_closed()
        
        self.clients_lock.release()
    
    
    async def get_client_names(self):
        # Request client names
        message = str(json.dumps({'command': 'get_client_names'}))
        message_size = len(message.encode(locale.getpreferredencoding())).to_bytes(8, 'big')
        self.writer.write(message_size + message.encode(locale.getpreferredencoding()))
        await self.writer.drain()
        
        # Get response
        response_size = int.from_bytes((await self.reader.readexactly(8)), 'big')
        response = json.loads((await self.reader.readexactly(response_size)).decode())
        
        # Parse response
        if all(key in response for key in ('command', 'status', 'client_names')):
            if response['command'] == 'get_client_names' and response['status'] == 'success':
                self.client_names = response['client_names']
                return
        
        self.client_names = None
    
    
    async def shutdown_host(self):
        async with self.clients_lock:
            for client in self.clients:
                if len(client) == 4:
                    client[-1].cancel()
        
        if self.register_task != None:
            self.register_task.cancel()
            self.register_task = None
        
        self.server = None
        self.addr = None
        self.port = None
        
        async with self.clients_lock:
            self.clients_list = list()
    
    
    async def shutdown_client(self):
        self.host_name = None
        self.host_addr = None
        self.host_port = None
        self.client_names = None
        
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
    locale.setlocale(locale.LC_ALL, '')
    stdscr = curses.initscr()
    curses.wrapper(main)
