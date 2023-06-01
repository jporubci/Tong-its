#!/usr/bin/env python3
# tong-its.py

# Import lobby.py
import lobby

# To shuffle the deck of cards
import secrets

### CONSTANTS ###

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

#END OF CONSTANTS


### OBJECTS ###

#points = min(max(1, RANKS.index(self.rank)), 10)
        
        
class Deck:
    def __init__(self):
        self.deck = [(rank, suit) for rank in RANKS for suit in SUITS]
        
    def shuffle(self):
        deck_copy = self.deck.copy()
        self.deck.clear()
        
        while deck_copy:
            card = secrets.choice(deck_copy)
            self.deck.append(card)
            deck_copy.remove(card)
        
        
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

#END OF OBJECTS


ret_val = lobby.main()

# Host
if type(ret_val) is dict:
    print('Host')
    
    while True:
        pass

# Client
elif type(ret_val) is tuple:
    print('Client')
    
    while True:
        pass
