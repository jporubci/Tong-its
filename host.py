#!/usr/bin/env python3
# host.py

# To handle connections and messages asynchronously
import asyncio

# To get host address and port
import socket

# To get catalog
import http.client

# os.getlogin() to get username
import os

# To send formatted registration messages
import json

# time.time_ns() to date messages
import time

# Predefined constants and helper functions
from config import Settings, get_message, send_message

class Host:
    def __init__(self):
        self.name = os.getlogin()
        self.server = None
        self.port = None
        
        self.register_task = None
        self.purge_task = None
        
        self.clients_lock = asyncio.Lock()
        self.clients = dict()
        
        self.refresh_flag = asyncio.Event()
        self.shutdown_flag = asyncio.Event()
    
    
    # Register with catalog server
    def register(self):
        socket.socket(socket.AF_INET, socket.SOCK_DGRAM).sendto(str(json.dumps({'type': Settings().ENTRY_TYPE, 'owner': self.name, 'port': self.port, 'num_clients': len(self.clients)})).encode(), (Settings().CATALOG_SERVER[:-5], int(Settings().CATALOG_SERVER[-4:])))
    
    
    # Register with catalog server every REGISTER_INTERVAL seconds
    async def register_coro(self):
        while not self.shutdown_flag.is_set():
            await asyncio.sleep(Settings().REGISTER_INTERVAL)
            self.register()
    
    
    # Handle incoming connection attempt from client
    async def handle_client(self, reader, writer):
        
        # Get join message
        message = await get_message(reader)
        
        # Check if lobby is not full
        async with self.clients_lock:
            if not (full := len(self.clients) == Settings().MAX_CLIENTS):
                # Accept new client
                join_time = time.time_ns() / 1000000000.0
                self.clients[(reader, writer)] = {
                                                    'name'      : message['name'],
                                                    'join_time' : join_time,
                                                    'last_ping' : join_time,
                                                    'shutdown'  : asyncio.Event()
                                                 }
                
                # Update catalog server
                self.register()
        
        # If lobby is full
        if full:
            # Reject client
            await send_message(writer, {'command': 'join', 'status': 'failure'})
            
            # Close connection
            writer.close()
            await writer.wait_closed()
            
            return
        
        # Send acceptance response
        if (await send_message(writer, {'command': 'join', 'status': 'success'}) == 0):
            # Trigger shutdown on this client handle
            self.clients[(reader, writer)]['shutdown'].set()
        
        # Set refresh_flag event to get lobbies
        self.refresh_flag.set()
        
        # Notify all clients to refresh
        async with self.clients_lock:
            for client in self.clients:
                if not self.clients[client]['shutdown'].is_set():
                    if (await send_message(client[1], {'command': 'refresh'}) == 0):
                        # Trigger shutdown on client handle
                        self.clients[client]['shutdown'].set()
        
        # Serve client until shutdown
        while not self.clients[(reader, writer)]['shutdown'].is_set():
            
            # Poll the shutdown flag while waiting for a message
            while not reader._buffer:
                await asyncio.sleep(0)
                if self.clients[(reader, writer)]['shutdown'].is_set():
                    break
            
            # Check shutdown flag another time
            if self.clients[(reader, writer)]['shutdown'].is_set():
                break
            
            # Get message now that we know the buffer is not empty from having polled it previously
            message = await get_message(reader)
            
            # Parse message
            if message['command'] == 'get_client_names':
                # Send a snapshot-copy of client names
                async with self.clients_lock:
                    clients_copy = [self.clients[client] for client in self.clients]
                
                clients_copy.sort(key=lambda x: x['join_time'])
                client_names = [client['name'] for client in clients_copy]
                
                if (await send_message(writer, {'command': 'get_client_names', 'status': 'success', 'client_names': client_names}) == 0):
                    # Trigger shutdown on this client handle
                    self.clients[(reader, writer)]['shutdown'].set()
            
            elif message['command'] == 'ping':
                # Update time last heard from client
                async with self.clients_lock:
                    self.clients[(reader, writer)]['last_ping'] = time.time_ns() / 1000000000.0
            
            elif message['command'] == 'leave':
                # Trigger shutdown for this client handler
                self.clients[(reader, writer)]['shutdown'].set()
                
            else:
                return
        
        # Shutdown
        writer.close()
        await writer.wait_closed()
        
        async with self.clients_lock:
            del self.clients[(reader, writer)]
            
            # Register with catalog to send update
            self.register()
            
            # Send refresh command
            for client in self.clients:
                if (await send_message(client[1], {'command': 'refresh'}) == 0):
                    # Trigger shutdown on client handle
                    self.clients[client]['shutdown'].set()
        
        # Set refresh_flag event to get lobbies
        self.refresh_flag.set()
    
    
    # Check clients' last pings every PING_INTERVAL seconds
    async def purge_coro(self):
        
        while not self.shutdown_flag.is_set():
            
            # Wait for PING_INTERVAL seconds
            await asyncio.sleep(Settings().PING_INTERVAL)
            stale_time = time.time_ns() / 1000000000.0 - (Settings().PING_INTERVAL + Settings().DELAY)
            
            async with self.clients_lock:
                # Record the starting number of clients before the purge
                num_clients = len(self.clients)
                
                # Check all pings
                for client in [client for client in self.clients]:
                    if not self.clients[client]['shutdown'].is_set():
                        if self.clients[client]['last_ping'] < stale_time:
                            # Kick client
                            await send_message(client[1], {'command': 'kick'})
                            
                            # Trigger shutdown for client handler
                            self.clients[client]['shutdown'].set()
                
                # If a client was kicked
                if len(self.clients) < num_clients:
                    
                    # Register with catalog to send update
                    self.register()
                    
                    # Send refresh command
                    for client in self.clients:
                        if (await send_message(client[1], {'command': 'refresh'}) == 0):
                            # Trigger shutdown on client handle
                            self.clients[client]['shutdown'].set()
                    
                    # Set refresh_flag event to get lobbies
                    self.refresh_flag.set()
    
    
    # Shutdown sequence
    async def shutdown(self):
        
        # Trigger host shutdown
        self.shutdown_flag.set()
        
        # Cancel all tasks
        self.register_task.cancel()
        self.purge_task.cancel()
        
        # Stop listening for new connections
        self.server.close()
        await self.server.wait_closed()
        
        # Trigger client handle shutdowns
        async with self.clients_lock:
            for client in self.clients:
                # Kick client
                await send_message(client[1], {'command': 'kick'})
                
                # Trigger shutdown for client handler
                self.clients[client]['shutdown'].set()
        
        # Wait for all clients to self-destruct; I'm too lazy to use a condition variable
        await self.clients_lock.acquire()
        while len(self.clients):
            self.clients_lock.release()
            await asyncio.sleep(0)
            await self.clients_lock.acquire()
        self.clients_lock.release()
        
        # Register a lie to make lobby disappear
        socket.socket(socket.AF_INET, socket.SOCK_DGRAM).sendto(str(json.dumps({'type': Settings().ENTRY_TYPE, 'owner': self.name, 'port': self.port, 'num_clients': Settings().MAX_CLIENTS + 1})).encode(), (Settings().CATALOG_SERVER[:-5], int(Settings().CATALOG_SERVER[-4:])))
