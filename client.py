#!/usr/bin/env python3

import http.client
import json
import time
import socket
import os

CATALOG_SERVER  = 'catalog.cse.nd.edu:9097'
ENTRY_TYPE      = 'Tong-its'
PING_INTERVAL   = 60
READ_BLOCK_SIZE = 1<<12
NUM_PLAYERS     = 3

class Client:
    def __init__(self):
        self.sock = None
        self.addr = None
        self.port = None
        
        
    # Retrieves list of lobbies
    def lookup(self):
        
        lobbies = list()
        
        # Get catalog
        http_conn = http.client.HTTPConnection(CATALOG_SERVER)
        http_conn.request('GET', '/query.json')
        
        # Parse catalog
        catalog = json.loads(http_conn.getresponse().read())
        http_conn.close()
        
        # Iterate through catalog
        for entry in catalog:
            
            # If the entry dict has the necessary keys
            if all(key in entry for key in ('type', 'address', 'port', 'lastheardfrom', 'owner', 'num_players')):
                
                # If the entry is an open lobby
                if entry['type'] == ENTRY_TYPE and entry['lastheardfrom'] >= time.time_ns() / 1000000000.0 - PING_INTERVAL and int(entry['num_players']) < NUM_PLAYERS:
                    
                    # Ensure entry is most recent entry of its kind
                    for lobby_entry in lobbies:
                        if lobby_entry['address'] == entry['address'] and lobby_entry['port'] == entry['port'] and lobby_entry['owner'] == entry['owner']:
                            if entry['lastheardfrom'] > lobby_entry['lastheardfrom']:
                                lobbies.remove(lobby_entry)
                    
                    if entry not in lobbies:
                        lobbies.append(entry)
        
        return lobbies
        
        
    def connect(self, addr, port):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((addr, port))
            self.addr = addr
            self.port = port
            
            return 1
        except:
            self.disconnect()
        
        
    def disconnect(self):
        self.sock.close()
        self.addr = None
        self.port = None
        
        
    def send_message(self, message):
        try:
            message_size = len(message.encode()).to_bytes(8, 'big')
            self.sock.sendall(message_size + message.encode())
            return 1
            
        except:
            self.disconnect()
            return 0
        
        
    def get_message(self):
        try:
            # Get message size
            message_size = int.from_bytes(self.sock.recv(8), 'big')
            
            # Get message
            message = ''
            bytes_read = 0
            while bytes_read < message_size:
                message += self.sock.recv(min(READ_BLOCK_SIZE, message_size - bytes_read)).decode()
                bytes_read += min(READ_BLOCK_SIZE, message_size - bytes_read)
                
            return json.loads(message)
        
        except:
            self.disconnect()
        
        
    # Attempt to join a lobby and get player number
    def join_lobby(self, lobby):
        
        # Try to connect to lobby host
        if self.connect(lobby['address'], lobby['port']) == 0:
            print('Unable to connect to lobby host\n\n')
            return 0
        
        # Send name to lobby host
        message = str(json.dumps({'name': os.getlogin()}))
        if self.send_message(message) == 0:
            print('Lost connection with the host\n\n')
            return 0
        
        # Get player number from host
        message = self.get_message()
        if self.sock:
            if 'player_num' in message:
                return int(message['player_num'])
        
        # Catch-all
        print('Unexpected error: could not get player number from host')
        return 0
        
        
    def drawCard(self, option):
        try:
            self.send_message(json.dumps({'command': 'drawCard', 'option': option}))
            response = self.get_message()
            
            return response
            
        except:
            print('Failed to get response.')
            self.disconnect()
            
        return None
        
        
    def expose(self, cards):
        try:
            self.send_message(json.dumps({'command': 'expose', 'cards': cards}))
            response = self.get_message()
            
            return response
            
        except:
            print('Failed to get response.')
            self.disconnect()
            
        return None
        
        
    def draw(self, cards):
        try:
            self.send_message(json.dumps({'command': 'draw'}))
            response = self.get_message()
            
            return response
            
        except:
            print('Failed to get response.')
            self.disconnect()
            
        return None
        
        
    def challenge(self):
        try:
            self.send_message(json.dumps({'command': 'challenge'}))
            response = self.get_message()
            
            return response
            
        except:
            print('Failed to get response.')
            self.disconnect()
            
        return None
        
        
    def fold(self):
        try:
            self.send_message(json.dumps({'command': 'fold'}))
            response = self.get_message()
            
            return response
            
        except:
            print('Failed to get response.')
            self.disconnect()
            
        return None
        
        
    def discardCard(self, card):
        try:
            self.send_message(json.dumps({'command': 'discardCard', 'card': card}))
            response = self.get_message()
            
            return response
            
        except:
            print('Failed to get response.')
            self.disconnect()
            
        return None
        
        
