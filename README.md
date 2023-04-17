# 2023 Copyright Timothy Borunov

prog: Peer to Peer Communication system using a client and discovery server.

Running the discovery server application should launch a discovery server object
which will act as a central hub for any clients. The server holds no message
data but contains a list of secure usernames and their IP addresses. When
a socket connects, the discovery server listens for a username and records
the users username and IP addresses. A user can then request another user by
name and that users open IP address and port will be sent back so that the
client application can handle communication directly.

Functionality not implemented yet:
-handling offline users
-handling server crash
-communication check

Client side communicates with a predefined discovery server to update current
IP address of the user and to request communication with other users.
Once discovery server responds with request user IP, the client side creates
a connection to that user.
Respectively, when a client receives communication, it creates a connection to
the user that just connected to it and sends the IP to discovery server which
will return the name of the person who connected or who will respond with no
such user to prompt the client to cut the connection since the connection was
established to an undefined user.
After connection is established, an open text channel exists between the two users

Functionality not implemented yet:
-multiple user connections
-handling offline users
-check user with discovery
-messaging interface and database

(server.py has some testing prompts from tests done before discovery server)