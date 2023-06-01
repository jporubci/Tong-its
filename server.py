#!/usr/bin/env python3
# table.py

# To shuffle the deck of cards
import secrets

# To get game constants
from config import Constants

class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        self.points = min(max(1, Constants().RANKS.index(self.rank)), 10)


class Player:
    def __init__(self, hand):
        self.hand = hand
        self.melds = list()
        self.score = None


class Server:
    def __init__(self):
        self.deck = self._init_deck()
        self.discard = list()
        self.order = self._init_order()
        self.players = self._init_players()
        self.last_draw = None
    
    
    # Returns a standard 52-card shuffled deck
    def _init_deck():
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
    def _init_players()
        players = [Player() for _ in range(Constants().NUM_PLAYERS)]
        for _ in range(Constants().STARTING_HAND_SIZE):
            for i in self.order:
                players[i].hand.append(self.deck.pop())
        
        for player in players:
            player.score = sum((card.points for card in player.hand))
        
        return players
