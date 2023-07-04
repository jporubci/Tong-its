#!/usr/bin/env python3
# server.py

# os.getlogin() to get host name
import os

# To shuffle the deck of cards
import secrets

# To get game constants
from config import Constants

class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        self.points = min(max(1, Constants().RANKS.index(self.rank)), 10)

# Decomposes cards
def decompose(cards):
    return [[card.rank, card.suit] for card in cards]

# Composes cards
def compose(cards):
    return [Card(card[0], card[1]) for card in cards]


class Player:
    def __init__(self, name):
        # Private
        self.hand = list()
        
        # Public
        self.name = name
        self.score = 0
        self.melds = list()
        self.can_draw = False
        
        #for player in players:
        #    player.score = sum((card.points for card in player.hand))


class Server:
    def __init__(self, clients):
        # Private
        self.deck = self._init_deck()
        
        # Public
        self.order = self._init_order()
        # Mixed
        self.players = self._init_players([(None, None, os.getlogin())]+clients)
        
        # Public
        self.discard = list()
        self.last_draw = None
        self.end = False
        
        # Player index
        self.turn = None
    
    
    # Returns a standard 52-card shuffled deck
    def _init_deck(self):
        temp_deck = [Card(rank, suit) for rank in Constants().RANKS for suit in Constants().SUITS]
        deck = list()
        while temp_deck:
            card = secrets.choice(temp_deck)
            deck.append(card)
            temp_deck.remove(card)
        
        return deck
    
    
    # Returns a random order of player indices
    def _init_order(self):
        temp_order = [i for i in range(Constants().NUM_PLAYERS)]
        order = list()
        while temp_order:
            index = secrets.choice(temp_order)
            order.append(index)
            temp_order.remove(index)
        
        return order
    
    
    # Deal cards to players
    def _init_players(self, clients):
        players = [Player(clients[i][2]) for i in range(Constants().NUM_PLAYERS)]
        for _ in range(Constants().STARTING_HAND_SIZE):
            for i in self.order:
                players[i].hand.append(self.deck.pop())
        
        return players
    
    
    # Reset the game
    def reset(self):
        self.deck = self._init_deck()
        self.discard = list()
        self.players = self._init_players()
        self.last_draw = None
