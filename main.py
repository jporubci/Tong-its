#!/usr/bin/env python3

import os
import http.client
import time
import json
import socket
import threading
import random

### CONSTANTS ###
#               #
CATALOG_SERVER  = 'catalog.cse.nd.edu:9097'

ENTRY_TYPE  = 'Tong-its'

PING_INTERVAL   = 60

READ_BLOCK_SIZE = 1<<12

NUM_PLAYERS  = 3

RANKS   = [
            'Ace', '1', '2', '3', '4',
            '5', '6', '7', '8', '9', '10',
            'Jack', 'Queen', 'King'
          ]

SUITS   = [ 'Clubs', 'Spades', 'Hearts', 'Diamonds' ]
#               #
#################


### OBJECTS ###
#             #
class Peer:
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
        for player_sock in self.player_sockets[1:]:
            try:
                player_sock.sendall(message)
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
        
        
class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        self.points = min(max(1, RANKS.index(self.rank)), 10)
        
        
class Deck:
    def __init__(self):
        self.deck = [Card(rank, suit) for rank in RANKS for suit in SUITS]
        
    def shuffle(self):
        random.shuffle(self.deck)
        
    def draw(self):
        if len(self.deck):
            return self.deck.pop()
        
        
class Discard:
    def __init__(self):
        self.discard = list()
        
    def put(self, card):
        if card:
            self.discard.append(card)
            return 1
        else:
            return 0
        
    def draw(self):
        if len(self.discard):
            return self.discard.pop()
        
        
class Player:
    def __init__(self):
        self.hand = list()
        
    def draw(self, card):
        if card:
            self.hand.append(card)
            return 1
        else:
            return 0
        
    # i is a string representing the index of the card in hand to discard
    def discard(self, i):
        if i.isnumeric() and int(i) < len(self.hand):
            return self.hand.pop(int(i))
#             #
###############


### GLOBALS ###
#             #
peer = Peer()

client = Client()

# 0 for host, 1 for client
identity = None

CURR_STATE  = None

DEALER  = None

# Tracks the last player to draw a card from the deck to settle draws
LAST_DRAW   = None
#             #
###############


def menu():
    global CURR_STATE
    
    print('q: quit\n0: host\n1: join\n')
    choice = input('> ')
    while all(option != choice for option in ('q', '0', '1')):
        print('Invalid option\n\n')
        return
    
    if choice == 'q':
        CURR_STATE = 'QUIT'
    elif choice == '0':
        CURR_STATE = 'HOST'
    elif choice == '1':
        CURR_STATE = 'JOIN'
    
    
# Host a lobby
def hostLobby():
    global peer, identity, CURR_STATE
    
    # Host lobby
    peer.host_lobby()
    
    # Broadcast to players that game is ready!
    message = str(json.dumps({'ready': '1'})).encode()
    message_size = len(message).to_bytes(8, 'big')
    
    if peer.broadcast_message(message_size + message) == 0:
        CURR_STATE = 'QUIT'
        return
    
    # Set identity to host and go to SETUP game state
    identity = 0
    CURR_STATE = 'SETUP'
    
    
# Join a lobby
def joinLobby():
    global client, identity, CURR_STATE
    
    # Get lobbies
    lobbies = client.lookup()
    
    # Print option select
    print('b: back to menu')
    print('r: refresh list')
    for i in range(len(lobbies)):
        print(str(i) + ': ' + lobbies[i]['owner'] + ' - ' + str(lobbies[i]['address']) + ':' + str(lobbies[i]['port']) + ' [' + str(lobbies[i]['players']) + '/3]')
    
    # Get option
    choice = input('> ')
    while not choice.isnumeric() or int(choice) >= len(lobbies):
        if choice == 'b':
            CURR_STATE = 'MENU'
            return
        elif choice == 'r':
            return
        
        print('Invalid option\n\n')
        return
        
    # Try to connect to the lobby of choice
    if not client.connect(lobbies[int(choice)]['address'], lobbies[int(choice)]['port']):
        print('Unable to connect to lobby\n\n')
        return
        
    else:
        # Send name to host
        message = str(json.dumps({'name': os.getlogin()}))
        
        if client.send_message(message) == 0:
            CURR_STATE = 'QUIT'
            return
        
        # Wait for game to start I guess
        print('Waiting for players...')
        message = client.get_message()
        
        if client.sock:
            if message['ready'] == '1':
                # Set identity to client and go to SETUP game state
                identity = 1
                CURR_STATE = 'SETUP'
    
    
def setup():
    global peer, client, identity, CURR_STATE
    
    if identity == 0:
        n = random.randrange(NUM_PLAYERS) + 1
        DEALER = 'PLAYER' + str(n)
        
        message = str(json.dumps({'dealer': str(n)})).encode()
        message_size = len(message).to_bytes(8, 'big')
        
        if peer.broadcast_message(message_size + message) == 0:
            CURR_STATE = 'QUIT'
            return
        
        CURR_STATE = DEALER
        
    elif identity == 1:
        message = client.get_message()
        
        n = int(message['dealer'])
        DEALER = 'PLAYER' + str(n)
        
    print('Player ' + str(n) + ' is the dealer!')
    
    
def player1():
    pass
    
    
def player2():
    pass
    
    
def player3():
    pass
    
    
def end():
    pass
    
    
def changeState():
    global CURR_STATE
    
    if CURR_STATE == 'MENU':
        menu()
    elif CURR_STATE == 'HOST':
        hostLobby()
    elif CURR_STATE == 'JOIN':
        joinLobby()
    elif CURR_STATE == 'SETUP':
        setup()
    elif CURR_STATE == 'PLAYER1':
        player1()
    elif CURR_STATE == 'PLAYER2':
        player2()
    elif CURR_STATE == 'PLAYER3':
        player3()
    elif CURR_STATE == 'END':
        end()
    elif CURR_STATE == 'QUIT':
        return
    else:
        return
    
    return 1
    
    
def displayState():
    global CURR_STATE
    
    #os.system('clear')
    
    
def main():
    global CURR_STATE
    
    CURR_STATE = 'MENU'
    while changeState():
        displayState()
    
    
### EXECUTION ###
main()
