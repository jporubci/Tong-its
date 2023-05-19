# Tong-its

TODO:

* Client leave implementation
* Client quit implementation
* Client catch ConnectionResetError Connection lost error 
* Host kick implementation
* Host disband implementation
* Host start implementation
* Host check time since last ping from client
* Host probably will need to catch ConnectionResetError Connection lost error as well, since client can disconnect within ping interval (ping is only auto-kick for disconnected clients)
* Host needs to end \_serve\_client() coroutine when client disconnects
