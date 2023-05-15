#!/usr/bin/env python3

import http.client
import json
import time
import socket

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
            if all(key in entry for key in ('type', 'address', 'port', 'lastheardfrom', 'owner', 'players')):
                
                # If the entry is an open lobby
                if entry['type'] == ENTRY_TYPE and entry['lastheardfrom'] >= time.time_ns() / 1000000000.0 - PING_INTERVAL and int(entry['players']) < NUM_PLAYERS:
                    
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
        
        
