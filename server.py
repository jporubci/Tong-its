#!/usr/bin/env python3

import socket
import threading
import json
import os

CATALOG_SERVER  = 'catalog.cse.nd.edu:9097'
ENTRY_TYPE      = 'Tong-its'
PING_INTERVAL   = 60
READ_BLOCK_SIZE = 1<<12
NUM_PLAYERS     = 3
    
class Server:
    def __init__(self):
        self.sock = None
        self.host = socket.gethostname()
        self.port = 0
        self.player_sockets = list()
        
        
    def host_lobby(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))
        self.port = self.sock.getsockname()[1]
        self.player_sockets.append((self.host, self.port))
        self.sock.listen(NUM_PLAYERS - 1)
        print(socket.gethostbyname(self.host) + ':' + str(self.port))
        
        print('Waiting for players...')
        
        # Register with the name server
        self.register()
        
        while len(self.player_sockets) < NUM_PLAYERS:
            client_sock, client_addr = self.sock.accept()
            self.player_sockets.append(client_sock)
            message = self.get_message(client_sock)
            print(message['name'] + ' joined')
            self.register(0)
        
        
    def register(self, timer=1):
        if timer == 1:
            threading.Timer(PING_INTERVAL, self.register).start()
        
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.sendto(json.dumps({'type': ENTRY_TYPE, 'owner': os.getlogin(), 'port': self.port, 'players': len(self.player_sockets)}).encode(), (CATALOG_SERVER[:-5], int(CATALOG_SERVER[-4:])))
        udp_socket.close()
        
        
    def broadcast_message(self, message):
        message_size = len(message).to_bytes(8, 'big')
        
        for player_sock in self.player_sockets[1:]:
            try:
                player_sock.sendall(message_size + message.encode())
            except:
                del self.player_sockets[1:]
                return 0
        
        return 1
        
        
    def get_message(self, player_sock):
        try:
            # Get message size
            message_size = int.from_bytes(player_sock.recv(8), 'big')
            
            # Get message
            message = ''
            bytes_read = 0
            while bytes_read < message_size:
                message += player_sock.recv(min(READ_BLOCK_SIZE, message_size - bytes_read)).decode()
                bytes_read += min(READ_BLOCK_SIZE, message_size - bytes_read)
                
            return json.loads(message)
        
        except:
            self.disconnect()
        
        
