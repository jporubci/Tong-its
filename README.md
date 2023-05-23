# Tong-its

TODO:

* Client catch ConnectionResetError Connection lost error 
* Host probably will need to catch ConnectionResetError Connection lost error as well, since client can disconnect within ping interval (ping is only auto-kick for disconnected clients)
* Consolidate incoming messages for the client in a single coroutine
* General code cleanup and modularization
* Use lobby.py as the foundation for the actual Tong-its game
