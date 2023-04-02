import sys
import socket
import selectors
import types
import select
import _thread
import pdb

class discover:
    def __init__(self, sock=None):
        self.discoverDict = {}
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock
        self.host = socket.gethostname()
        self.port = 60001
        self.sock.bind((self.host,self.port))
        print("Discover server has started")
        print("Awaiting clients")
        self.sock.setblocking(0)
        
        self.sock.listen()
        while True:
            conn, addr = self.sock.accept()
            _thread.start_new_thread(update_map,(conn,addr))
        
    def update_map(conn,addr):
        while True:
            msg = conn.recv(1024).decode()
            print(addr,msg)
            if not data:
                break
            

    def read_map():

    
