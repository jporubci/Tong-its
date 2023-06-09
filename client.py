#!/usr/bin/env python3
# client.py

# To handle connections and messages asynchronously
import asyncio

# os.getlogin() to get username
import os

# time.time_ns() to date messages
import time

# Predefined constants and helper functions
from config import Settings, get_message, send_message

class Client:
    def __init__(self):
        self.name = os.getlogin()
        
        self.host_name = None
        self.client_names = None
        
        self.reader = None
        self.writer = None
        
        self.listen_task = None
        self.ping_task = None
        
        self.refresh_flag = asyncio.Event()
        self.shutdown_flag = asyncio.Event()
        self.start_flag = asyncio.Event()
    
    
    # Listen to host
    async def listen_coro(self):
        while not self.shutdown_flag.is_set():
            
            # Poll the shutdown flag while waiting for a message
            while not self.reader._buffer:
                await asyncio.sleep(0)
                if self.shutdown_flag.is_set():
                    return
            
            # Check shutdown flag another time
            if self.shutdown_flag.is_set():
                break
            
            # Get message now that we know the buffer is not empty from having polled it previously
            message = await get_message(self.reader)
            
            # Parse message
            if message['command'] == 'get_client_names':
                # Set client names
                if message['status'] == 'success':
                    self.client_names = message['client_names']
                    
                    # Set refresh_flag event to refresh display
                    self.refresh_flag.set()
                    
                else:
                    self.client_names = None
            
            elif message['command'] == 'refresh':
                # Get client names
                if (await send_message(self.writer, {'command': 'get_client_names'}) == 0):
                    # Trigger shutdown
                    self.shutdown_flag.set()
                
                # Set refresh_flag event to get lobbies
                self.refresh_flag.set()
            
            elif message['command'] == 'kick':
                # Trigger shutdown for this listen task
                self.shutdown_flag.set()
            
            elif message['command'] == 'start':
                # Set start flag
                self.start_flag.set()
                return
        
        # Shutdown
        self.writer.close()
        await self.writer.wait_closed()
    
    
    # Ping host every PING_INTERVAL seconds
    async def ping_coro(self):
        while not self.shutdown_flag.is_set():
            
            # Wait for PING_INTERVAL seconds
            await asyncio.sleep(Settings().PING_INTERVAL)
            
            # Ping host
            if (await send_message(self.writer, {'command': 'ping'}) == 0):
                # Trigger shutdown
                self.shutdown_flag.set()
    
    
    # Shutdown sequence
    async def shutdown(self):
        
        # Trigger client shutdown
        self.shutdown_flag.set()
        
        # Wait for listen task and cancel ping task
        if self.listen_task != None:
            await self.listen_task
        if self.ping_task != None:
            self.ping_task.cancel()
