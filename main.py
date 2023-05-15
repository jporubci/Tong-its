#!/usr/bin/env python3

import os
import json
import random

from server import Server
from client import Client

### CONSTANTS ###
#               #
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
        # Whether player acts as a server or a client
        self.server = None
        self.client = None
        
        # 1 or 2 or 3
        self.number = None
        
        # list of Card objects
        self.hand = list()
        
        
    def setIdentity(self, identity=''):
        if identity == 'SERVER':
            self.server = Server()
            self.client = None
        elif identity == 'CLIENT':
            self.client = Client()
            self.server = None
        else:
            self.server = None
            self.client = None
        
        
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
player = Player()

CURR_STATE  = None

DEALER  = None

# Tracks the last player to draw a card from the deck to settle draws
LAST_DRAW   = None
#             #
###############


def menu():
    global player, CURR_STATE
    
    print('q: quit\n0: host\n1: join\n')
    choice = input('> ')
    while all(option != choice for option in ('q', '0', '1')):
        print('Invalid option\n')
        return
    
    if choice == 'q':
        CURR_STATE = 'QUIT'
        
    elif choice == '0':
        # Set player identity to server
        player.setIdentity('SERVER')
        
        CURR_STATE = 'HOST'
        
    elif choice == '1':
        # Set player identity to client
        player.setIdentity('CLIENT')
        
        CURR_STATE = 'JOIN'
    
    
# Host a lobby
def hostLobby():
    global player, CURR_STATE
    
    # Host lobby
    if player.server.host_lobby() == 0:
        print('Failed to start game\n')
        
        # Reset identity to unknown
        player.setIdentity()
        CURR_STATE = 'MENU'
        return
    
    CURR_STATE = 'SETUP'
    
    
# Join a lobby
def joinLobby():
    global player, CURR_STATE
    
    # Get lobbies
    lobbies = player.client.lookup()
    
    # Print option select
    print('b: back to menu')
    print('r: refresh list')
    for i in range(len(lobbies)):
        print(str(i) + ': ' + lobbies[i]['owner'] + ' - ' + str(lobbies[i]['address']) + ':' + str(lobbies[i]['port']) + ' [' + str(lobbies[i]['num_players']) + '/' + str(NUM_PLAYERS) +  ']')
    
    # Get option
    choice = input('> ')
    if not choice.isnumeric() or int(choice) >= len(lobbies):
        if choice == 'b':
            # Reset identity to unknown
            player.setIdentity()
            CURR_STATE = 'MENU'
            return
            
        if choice == 'r':
            return
        
        print('Invalid option\n')
        return
        
    # Try to connect to the lobby of choice
    player.number = player.client.join_lobby(lobbies[int(choice)])
    
    if player.number < 2 or player.number > NUM_PLAYERS:
        return
    
    # Wait for game to start I guess
    print('Waiting for players...')
    message = player.client.get_message()
    
    if player.client.sock:
        if 'ready' in message and message['ready'] == '1':
            CURR_STATE = 'SETUP'
            return
    
    print('Unexpected error: I have no idea')
    player.setIdentity()
    CURR_STATE = 'MENU'
    
    
def setup():
    global player, CURR_STATE
    
    if player.server:
        player.number = 1
        
        n = random.randrange(NUM_PLAYERS) + 1
        DEALER = 'PLAYER' + str(n)
        
        message = str(json.dumps({'dealer': str(n)}))
        
        if player.server.broadcast_message(message) == 0:
            print('Failed to send a message to a player')
            player.setIdentity()
            CURR_STATE = 'MENU'
            return
        
    elif player.client:
        message = player.client.get_message()
        
        if 'dealer' in message:
            n = int(message['dealer'])
            DEALER = 'PLAYER' + str(n)
        
    else:
        print('Unexpected error: player is neither server nor client in SETUP state')
        player.setIdentity()
        CURR_STATE = 'MENU'
        return
        
    print('You are player ' + str(player.number))
    print('Player ' + str(n) + ' is the dealer!')
    CURR_STATE = DEALER
    
    
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
