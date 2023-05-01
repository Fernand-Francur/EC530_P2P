# Copyright 2023 Timothy Borunov timobohr@bu.edu

prog: Peer to Peer Communication system using a client and discovery server.

discovery.py:

RUN: python3 discovery.py (ip) (port)

Running the discovery server application launches a discovery server object
which will act as a central hub for any clients. The server holds no message
data but contains a list of secure usernames, their IP addresses, and connections. When
a socket connects, the discovery server listens for a username and records
the users username and IP addresses. A user can then request another user by
name and that users open IP address and port will be sent back so that the
client application can handle communication directly.

At the current time discovery server defaults to setting up on local host but
a specific IP and port can be specified. Clients can then specify to connect to
the specific ip and port.

List of functionality:
-Database of last known user ip and ports
-Database of all known user connections
-Clients can request other users to send messages
-Provides updates on client status
-Close by ctrl+c (exits quietly)
-Defence against SQL injections

Unimplemented
-No username uniqueness and account cybersecurity
-No recovery attempts on crash

client.py:

RUN: python3 client.py username port (ip) (discovery server ip) (discovery server port)

Client side communicates with a specified discovery server to update current
IP address of the user and to request communication with other users. Client
defaults to trying to use a discovery server on localhost with a default port number.
Once discovery server responds with request user IP, the client side creates
a connection to that user.

Respectively, when a client receives communication, it creates a connection to
the user that just connected to it and sends the IP to discovery server which
will return the name of the person who connected or who will respond with no
such user to prompt the client to cut the connection since the connection was
established to an undefined user.
After connection is established, an open text channel exists between the two users

List of Functionality:
-Running creates a client chat box with specified username and immediately
notifies discovery server.
-REQUEST <user> can be called to create a communication channel directly between the
user who requested and the user who is contacted by asking the discovery server for
user connection information (only creates connection if user exists)
-CHAT <user> <message> used to send message to particular known user
-LOGOUT to close client
-FULL OFFLINE SUPPORT! If a client becomes offline, messages can be still be sent to that
user and connections can be requested, but will not be processed until both chatters/requesters
are online as messages are buffered locally at each user, and connections are communicated by
discovery server. So no messages if any users go offline are lost
-Even if discovery server crashes, existing connections are still available (hence why this
is peer to peer), but no new connections can be made

Unimplemented:
-chatrooms
-cybersecurity for separate accounts


