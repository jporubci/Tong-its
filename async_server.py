#!/usr/bin/env python3

# async_main.py

import asyncio
import time
import os
import json
import http.client
import socket

class Host:
    def __init__(self, player):
        self.ENTRY_TYPE = 'Tong-its'
        self.CATALOG_SERVER = 'catalog.cse.nd.edu:9097'
        self.REGISTER_INTERVAL = 60
        self.PING_INTERVAL = 5
        self.DELAY = 1
        self.MIN_CLIENTS = 2
        self.MAX_CLIENTS = 2
        
        self.prev_state = player.prev_state
        self.curr_state = player.curr_state
        self.name = player.name
        
        self.server = None
        self.addr = None
        self.port = None
        
        self.clients = list()
        self.clients_lock = asyncio.Lock()
    
    
    async def host(self):
        if self.prev_state == 'MENU':
            # Program listens for incoming connections
            self.server = await asyncio.start_server(self._handle_client, host=socket.gethostname(), backlog=self.MAX_CLIENTS)
            
            self.addr = self.server.sockets[0].getsockname()[0]
            self.port = self.server.sockets[0].getsockname()[1]
            
            # Try to register with catalog server
            if self._register() == 0:
                return 'QUIT'
            
            # Register every REGISTER_INTERVAL seconds
            asyncio.create_task(self._register_interval())
            
        lobbies = await self._display_lobbies()
        
        print()
        print(self.name)
        # TODO: Display enumerated client names
        #
        print()
        
        print('r: refresh')
        print('d: disband')
        print('s: start')
        print('q: quit')
        
        choice = input('\n> ')
        print()
        while not choice.isnumeric() or int(choice) > len(lobbies) or choice == '0':
            if choice == 'r':
                return 'HOST'
                
            elif choice == 'd':
                # TODO: Implement disband
                pass
            
            if choice == 's':
                # TODO: Implement start
                pass
            
            elif choice == 'q':
                return 'QUIT'
            
            print('Invalid option')
            choice = input('\n> ')
            print()
        
        # TODO: Implement kick
        
        return 'HOST'
    
    
    async def _handle_client(self, reader, writer):
        # Read first 8 bytes to get message size
        message_size = (await reader.readexactly(8)).decode()
        
        # Get client name
        client_name = (await reader.readexactly(message_size)).decode()
        
        async with self.clients_lock:
            self.clients.append((client_name, reader, writer))
            self._register()
    
    
    # Requires self.clients_lock
    def _register(self):
        # Try to register with catalog server
        try:
            return socket.socket(socket.AF_INET, socket.SOCK_DGRAM).sendto(json.dumps({'type': self.ENTRY_TYPE, 'owner': os.getlogin(), 'port': self.port, 'num_clients': len(self.clients)}).encode(), (self.CATALOG_SERVER[:-5], int(self.CATALOG_SERVER[-4:])))
        
        except:
            self._register_fail()
            return 0
    
    
    async def _register_interval(self):
        while True:
            # Register with catalog server every REGISTER_INTERVAL seconds
            await asyncio.sleep(self.REGISTER_INTERVAL)
            async with self.clients_lock:
                self._register()
    
    
    def _register_fail(self):
        print('Fatal error: failed to register with catalog server')
        input('Press any key to end program\n')
    
    
    async def _display_lobbies(self):
        # Try to get catalog within time limit
        try:
            response = await asyncio.wait_for(self._get_catalog(), timeout=self.DELAY)
            
            '''
            async with asyncio.timeout(DELAY):
                response = await self._get_catalog()
            '''
        
        except TimeoutError:
            self._get_catalog_fail()
            return 0
        
        # Parse response body
        lobbies = self._parse_catalog(response)
        
        # Display lobbies
        for lobby in lobbies:
            print(f'{lobby["owner"]} - {lobby["address"]}:{lobby["port"]} [{lobby["num_clients"]}/{self.MAX_CLIENTS}]')
        
        return lobbies


    async def _get_catalog(self):
        http_conn = http.client.HTTPConnection(self.CATALOG_SERVER)
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
                if entry['type'] == self.ENTRY_TYPE and entry['lastheardfrom'] >= time.time_ns() / 1000000000.0 - self.REGISTER_INTERVAL and entry['num_clients'] < self.MAX_CLIENTS:
                    
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
        
        return lobbies


    def _get_catalog_fail():
        print('Fatal error: failed to get catalog from catalog server')
        input('Press any key to end program\n')


class Client:
    ENTRY_TYPE = 'Tong-its'
    CATALOG_SERVER = 'catalog.cse.nd.edu:9097'
    REGISTER_INTERVAL = 60
    PING_INTERVAL = 5
    DELAY = 1
    MIN_CLIENTS = 2
    MAX_CLIENTS = 2
    
    def __init__(self, player):
        self.prev_state = player.prev_state
        self.curr_state = player.curr_state
        self.name = player.name
        self.reader = player.reader
        self.writer = player.writer
        
        #


class Player:
    def __init__(self):
        self.ENTRY_TYPE = 'Tong-its'
        self.CATALOG_SERVER = 'catalog.cse.nd.edu:9097'
        self.REGISTER_INTERVAL = 60
        self.PING_INTERVAL = 5
        self.DELAY = 1
        self.MIN_CLIENTS = 2
        self.MAX_CLIENTS = 2
        
        self.prev_state = None
        self.curr_state = 'MENU'
        self.name = os.getlogin()
        
        # Client
        self.reader = None
        self.writer = None
    
    
    async def menu(self):
        lobbies = await self._display_lobbies()
        print('0: host')
        print('r: refresh')
        print('q: quit')
        
        choice = input('\n> ')
        print()
        while not choice.isnumeric() or int(choice) > len(lobbies):
            if choice == 'r':
                return 'MENU'
                
            elif choice == 'q':
                return 'QUIT'
            
            print('Invalid option')
            choice = input('\n> ')
            print()
        
        if choice == '0':
            return 'HOST'
        
        # Try to connect to chosen lobby
        lobby = lobbies[int(choice) - 1]
        self.reader, self.writer = await asyncio.open_connection(lobby['address'], lobby['port'])
        
        # Send name to host
        message = str(json.dumps({'command': 'join', 'name': os.getlogin()}))
        message_size = len(message.encode()).to_bytes(8, 'big')
        self.writer.write(message_size + message.encode())
        await self.writer.drain()
        
        return 'WAITING'


    async def _display_lobbies(self):
        # Try to get catalog within time limit
        try:
            response = await asyncio.wait_for(self._get_catalog(), timeout=self.DELAY)
            
            '''
            async with asyncio.timeout(DELAY):
                response = await self._get_catalog()
            '''
        
        except TimeoutError:
            self._get_catalog_fail()
            return 0
        
        # Parse response body
        lobbies = self._parse_catalog(response)
        
        # Display lobbies
        for i, lobby in enumerate(lobbies, start=1):
            print(f'{i}: {lobby["owner"]} - {lobby["address"]}:{lobby["port"]} [{lobby["num_clients"]}/{self.MAX_CLIENTS}]')
        
        return lobbies


    async def _get_catalog(self):
        http_conn = http.client.HTTPConnection(self.CATALOG_SERVER)
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
                if entry['type'] == self.ENTRY_TYPE and entry['lastheardfrom'] >= time.time_ns() / 1000000000.0 - self.REGISTER_INTERVAL and entry['num_clients'] < self.MAX_CLIENTS:
                    
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
        
        return lobbies


    def _get_catalog_fail():
        print('Fatal error: failed to get catalog from catalog server')
        input('Press any key to end program\n')


async def main():
    player = Player()
    
    while player.curr_state != 'QUIT':
        
        if player.curr_state == 'MENU':
            
            if player.prev_state == 'HOST' or player.prev_state == 'WAITING':
                player = Player()
            
            next_state = await player.menu()
        
        elif player.curr_state == 'HOST':
            
            if player.prev_state == 'MENU':
                player = Host(player)
            
            next_state = await player.host()
        
        elif player.curr_state == 'WAITING':
            
            if player.prev_state == 'MENU':
                player = Client(player)
            
            next_state = await player.waiting()
        
        elif player.curr_state == 'SETUP':
            next_state = await player.setup()
        
        else:
            print(f'Fatal error: undefined state \'{player.curr_state}\'')
            next_state = 'QUIT'
        
        player.prev_state = player.curr_state
        player.curr_state = next_state


# Execution
asyncio.run(main())
