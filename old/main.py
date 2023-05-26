#!/usr/bin/env python3

import os
import json
import random

from server import Server
from client import Client

### CONSTANTS ###
#               #
NUM_PLAYERS  = 3

STARTING_HAND_SIZE = 12

RANKS   = [
            'A', '2', '3', '4', '5', '6', '7',
            '8', '9', '10', 'J', 'Q', 'K'
          ]

CLUB    = '\U00002660'
SPADE   = '\U00002663'
HEART   = '\U00002665'
DIAMOND = '\U00002666'

SUITS   = [ CLUB, SPADE, HEART, DIAMOND ]
#               #
#################


### OBJECTS ###
#             #
class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        self.points = min(max(1, RANKS.index(self.rank)), 10)
    
    def decompose(self):
        return (self.rank, self.suit)
        
        
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
        
        # Server will have deck
        self.deck = None
        
        # 1 or 2 or 3
        self.number = None
        
        # list of Card objects
        self.hand = None
        
        
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
        
        
    def composeHand(self, hand_data):
        self.hand = [Card(card_data[0], card_data[1]) for card_data in hand_data]
        
        
    # Display hand in a column or a row
    def displayHand(self, option):
        self.hand.sort(key=lambda x: x.suit)
        self.hand.sort(key=lambda x: RANKS.index(x.rank))
        
        if option == 'col':
            for i in range(len(self.hand)):
                print(f'{i:2d}: {self.hand[i].rank.rjust(2)}{self.hand[i].suit}')
            
        elif option == 'row':
            if len(self.hand) > 0:
                print(f'{self.hand[0].rank.rjust(2)}{self.hand[0].suit}', end='')
                
            for i in range(1, len(self.hand)):
                print(f' {self.hand[i].rank.rjust(2)}{self.hand[i].suit}', end='')
            
            print()
#             #
###############


### GLOBALS ###
#             #
player = Player()

# List of player names
names = list()

# Index for names for whose turn it is
turn = None

CURR_STATE = None

# Tracks the last player to draw a card from the deck to settle draws
last_draw = None
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
    global player, names, CURR_STATE
    
    # Host lobby
    names, ret_val = player.server.host_lobby()
    
    if ret_val == 0:
        names = list()
        
        print('Failed to start game\n')
        
        # Reset identity to unknown
        player.setIdentity()
        CURR_STATE = 'MENU'
        return
    
    CURR_STATE = 'SETUP'
    
    
# Join a lobby
def joinLobby():
    global player, names, CURR_STATE
    
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
    
    if player.number < 1 or player.number >= NUM_PLAYERS:
        return
    
    # Wait for game to start I guess
    print('Waiting for players...')
    message = player.client.get_message()
    
    if player.client.sock:
        if 'ready' in message and message['ready'] == '1':
            if 'names' in message:
                names = message['names']
                CURR_STATE = 'SETUP'
                return
    
    print('Unexpected error: I have no idea')
    player.setIdentity()
    CURR_STATE = 'MENU'
    
    
def setup():
    global player, names, turn, CURR_STATE
    
    if player.server:
        # Set own player number
        player.number = 0
        
        # Set state to first player
        turn = random.randrange(NUM_PLAYERS)
        
        # Broadcast first player
        message = str(json.dumps({'turn': str(turn)}))
        
        if player.server.broadcast_message(message) == 0:
            print('Failed to send a message to a player')
            player.setIdentity()
            CURR_STATE = 'MENU'
            return
        
        # Deal the cards
        player.server.deck = Deck()
        player.server.discard = Discard()
        player.server.deck.shuffle()
        
        hands = list()
        for i in range(NUM_PLAYERS):
            hands.append(list())
        
        for i in range(STARTING_HAND_SIZE):
            for j in range(NUM_PLAYERS):
                hands[j].append(player.server.deck.draw().decompose())
        
        # Send hands to players
        for i in range(1, NUM_PLAYERS):
            message = str(json.dumps({'hand': hands[i]}))
            
            if player.server.send_message(player.server.player_sockets[i], message) == 0:
                print('Failed to send hand to ' + names[i])
                player.setIdentity()
                CURR_STATE = 'MENU'
                return
        
        # Set own hand
        player.composeHand(hands[0])
        
    elif player.client:
        
        # Receive who's first
        message = player.client.get_message()
        
        if 'turn' in message:
            turn = int(message['turn'])
        
        # Receive hand from server
        hand_data = player.client.get_message()
        
        if 'hand' in hand_data:
            player.composeHand(hand_data['hand'])
        
    else:
        print('Unexpected error: player is neither server nor client in SETUP state')
        player.setIdentity()
        CURR_STATE = 'MENU'
        return
        
    os.system('clear')
    #print(names[turn] + ' goes first!')
    CURR_STATE = 'PLAYER_TURN'
    
    
def drawPhase():
    global player, turn, CURR_STATE
    
    # Get deck and discard count
    if player.server:
        deck_size = len(player.server.deck.deck)
        discard_size = len(player.server.discard.discard)
        
        if discard_size > 0:
            discard_top = player.server.discard.discard[0].decompose()
        else:
            discard_top = (None, None)
        
        message = str(json.dumps({'deck_size': str(deck_size), 'discard_size': str(discard_size), 'discard_top': discard_top}))
        
        if player.server.broadcast_message(message) == 0:
            print('Failed to send a message to a player')
            player.setIdentity()
            CURR_STATE = 'MENU'
            return
    
    elif player.client:
        message = player.client.get_message()
        
        if 'deck_size' in message and 'discard_size' in message:
            deck_size = int(message['deck_size'])
            discard_size = int(message['discard_size'])
            discard_top = message['discard_top']
            
    else:
        print('Unexpected error: player is neither server nor client in SETUP state')
        player.setIdentity()
        CURR_STATE = 'MENU'
        return
    
    # Base case
    if deck_size == 0:
        CURR_STATE = 'END'
        return
    
    # Display deck and discard sizes
    print(f'Deck ({deck_size})')
    
    if discard_size > 0:
        print(f'Discard ({discard_size}): {discard_top[0]}{discard_top[1]}\n')
    else:
        print(f'Discard ({discard_size})')
    
    # Display hand
    print()
    player.displayHand('row')
    print()
    
    # Display whose turn it is
    if player.number == turn:
        print('Your turn\n')
        
        actions = list()
        # Display possible actions
        if deck_size > 0:
            print(f'{len(actions)}: Draw a card from the deck')
            actions.append('drawCard deck')
        
        # CONTINUE ACTIONS HERE: EXPOSE, ETC
        
            
        return actions
        
    else:
        print(names[turn] + '\'s turn\n')
        
        return []
    
    
def player_turn():
    global player, turn, CURR_STATE, last_draw
    
    actions = drawPhase()
    
    # Your turn
    if len(actions) > 0:
        # Get option
        choice = input('> ')
        while not choice.isnumeric() or int(choice) >= len(actions):
            print('Invalid option\n')
            choice = input('> ')
            
        if actions[int(choice)] == 'drawCard deck':
            c = player.client.drawCard('deck')
            player.hand.append(Card(c[0], c[1]))
        
        elif actions[int(choice)] == 'drawCard discard':
            c = player.client.drawCard('discard')
            player.hand.append(Card(c[0], c[1]))
            
        last_draw = player.name
        
        
        # Client operations:
        # drawCard(option) - Draw from deck or discard pile
        # expose(cards) - Expose meld
        # draw() - Propose a draw
        # challenge() - Accept the draw
        # fold() - Decline the draw
        # discardCard(card) - Discard a card
        
        # Server responses:
        # drawCard(option) - Returns a decomposed card on success, otherwise failure
        # expose(cards) - Returns success, otherwise failure
        # draw() - Returns success, otherwise failure
        # challenge() - Returns success, otherwise failure
        # fold() - Returns success, otherwise failure
        # discardCard(card) - Returns success, otherwise failure
        
        while(True):
            pass
        
    # Someone else's turn
    elif len(actions) == 0:
        # Wait for client
        if player.server:
            print('Waiting for client')
            while(True):
                pass
            
        # Wait for server
        elif player.client:
            print('Waiting for server')
            while(True):
                pass
        
    # Error, probably going back to MENU state
    else:
        return
    
    
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
    elif CURR_STATE == 'PLAYER_TURN':
        player_turn()
    elif CURR_STATE == 'END':
        end()
    elif CURR_STATE == 'QUIT':
        return
    else:
        return
    
    return 1
    
    
def main():
    global CURR_STATE
    
    CURR_STATE = 'MENU'
    while changeState():
        pass
    
    
### EXECUTION ###
main()
