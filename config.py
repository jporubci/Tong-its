#!/usr/bin/env python3
# config.py

import json

# Returns message as dict
async def get_message(reader):
    message_size = int.from_bytes((await reader.readexactly(8)), 'big')
    return json.loads((await reader.readexactly(message_size)).decode())


# Sends a message
async def send_message(writer, message_json):
    message = str(json.dumps(message_json)).encode()
    message_size = len(message).to_bytes(8, 'big')
    
    try:
        writer.write(message_size + message)
        await writer.drain()
        return 1
        
    except (ConnectionResetError, BrokenPipeError):
        return 0


class Settings:
    def __init__(self):
        self.ENTRY_TYPE = 'Tong-its'
        self.CATALOG_SERVER = 'catalog.cse.nd.edu:9097'
        self.REGISTER_INTERVAL = 30
        self.PING_INTERVAL = 1
        self.DELAY = 1
        self.MIN_CLIENTS = 2
        self.MAX_CLIENTS = 2


class Constants:
    def __init__(self):
        self.NUM_PLAYERS        = 3
        self.STARTING_HAND_SIZE = 12
        
        self.RANKS      = [
                            'A', '2', '3', '4', '5', '6', '7',
                            '8', '9', '10', 'J', 'Q', 'K'
                          ]
        
        self.CLUB       = '\U00002660'
        self.SPADE      = '\U00002663'
        self.HEART      = '\U00002665'
        self.DIAMOND    = '\U00002666'
        self.SUITS      = [ self.CLUB, self.SPADE, self.HEART, self.DIAMOND ]
