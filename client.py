#!/usr/bin/env python3
# client.py

# To handle connections and messages asynchronously
import asyncio

# os.getlogin() to get username
import os

# To send and receive data structures via messages
import json

# time.time_ns() to date messages
import time

# Predefined constants
from config import Settings

class Client:
    def __init__(self):
        self.name = os.getlogin()
        self.settings = Settings()
        
        self.host_name = None
        
        self.reader = None
        self.writer = None
        
        self.listen_task = None
        self.ping_task = None
        
        self.shutdown_flag = asyncio.Event()
    
    
    # Returns message as dict
    async def get_message(reader):
        message_size = int.from_bytes((await reader.readexactly(8)), 'big')
        return json.loads((await reader.readexactly(message_size)).decode())
    
    
    # Sends a message
    async def send_message(writer, message_json):
        message = str(json.dumps(message_json)).encode()
        message_size = len(message).to_bytes(8, 'big')
        writer.write(message_size + message)
        await writer.drain()
    
    
    # Listen to host
    async def listen_task(self):
        while not self.shutdown_flag.is_set():
            
            # Poll the shutdown flag while waiting for a message
            while not self.reader._buffer:
                if self.shutdown_flag.is_set():
                    return
            
            # Check shutdown flag another time
            if self.shutdown_flag.is_set():
                break
            
            # Get message now that we know the buffer is not empty from having polled it previously
            message = await self.get_message(self.reader)
            
            # Parse message
            if message['command'] == 'get_client_names':
                # Set client names
                if message['status'] == 'success':
                    self.client_names = message['client_names']
                else:
                    self.client_names = None
            
            elif message['command'] == 'refresh':
                # Get client names
                await self.send_message(self.writer, {'command': 'get_client_names'})
                
                # Set refresh_flag event to get lobbies
                self.refresh_flag.set()
            
            elif message['command'] == 'kick':
                # Trigger shutdown for this listen task
                self.shutdown_flag.set()
        
        # Shutdown
        self.writer.close()
        await self.writer.wait_closed()
    
    
    # Ping host every PING_INTERVAL seconds
    async def ping_task(self):
        while not self.shutdown_flag.is_set():
            
            # Wait for PING_INTERVAL seconds
            await asyncio.sleep(self.settings.PING_INTERVAL)
            
            # Ping host
            await self.send_message(self.writer, {'command': 'ping'})
    
    
    # Shutdown sequence
    async def shutdown(self):
        
        # Trigger client shutdown
        self.shutdown_flag.set()
        
        # Wait for all tasks to return
        await self.listen_task
        await self.ping_task
