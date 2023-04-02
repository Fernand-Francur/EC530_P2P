import sys
import socket
import selectors
import types
import select
import pdb 

class Peer2PeerClient:
    def __init__(self, username, discover_host=None, discover_port=None):
        if discover_host is None:
            self.discover_host = socket.gethostname()
        else:
            self.discover_host = discover_host
        if discover_port is None:
            self.discover_port = 60001
        else:
            self.discover_port = discover_port
        self.discover_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.discover_socket.connect((self.discover_host,discover_port))
        self.discover_socket.send(('1' + username).encode)
        
        data = self.discover_socket.recv(1024).decode()
        
        
    def connect():

    def send():

    




"""
def start_connections(host, port, num_conns):
    sel = selectors.DefaultSelector()
    messages1 = [b"Message 1 from client.", b"Message 2 from client."]
    server_addr = (host, port)
    for i in range(0, num_conns):
        connid = i + 1
        print(f"Starting connection {connid} to {server_addr}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        sock.connect_ex(server_addr)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        data1 = types.SimpleNamespace(
            connid=connid,
            msg_total=sum(len(m) for m in messages1),
            recv_total=0,
            messages=messages1.copy(),
            outb=b"",
        )
        sel.register(sock, events, data=data1)

host, port, num = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
start_connections

import socket

HOST = "127.0.0.1"  # The server's hostname or IP address
PORT = 65432  # The port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b"Hello, world")
    data = s.recv(1024)

print(f"Received {data!r}")
"""
