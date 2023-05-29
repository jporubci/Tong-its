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
