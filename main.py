#!/usr/bin/env python3

import os
import http.client
import time
import json
import socket
import random

from server import Server
from client import Client

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
server = Server()

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
    global server, identity, CURR_STATE
    
    # Host lobby
    server.host_lobby()
    
    # Broadcast to players that game is ready!
    message = str(json.dumps({'ready': '1'}))
    
    if server.broadcast_message(message) == 0:
        CURR_STATE = 'QUIT'
        return
    
    # Set identity to host and go to SETUP game state
    identity = 0
    CURR_STATE = 'SETUP'
    
    
    message_size = len(message).to_bytes(8, 'big')
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
    global server, client, identity, CURR_STATE
    
    if identity == 0:
        n = random.randrange(NUM_PLAYERS) + 1
        DEALER = 'PLAYER' + str(n)
        
        message = str(json.dumps({'dealer': str(n)}))
        
        if server.broadcast_message(message) == 0:
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
