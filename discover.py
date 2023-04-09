import sys
import socket
import types
import select
import _thread
import pdb

PORT = 60001
HEAD_LEN = 16

class discover:
    def __init__(self, sock=None):
        self.discoverDict = {}
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
        self.host = socket.gethostname()
        self.port = PORT
        self.sock.bind((self.host,self.port))
        print("Discover server has started")
        print("Awaiting clients")
        self.sock.setblocking(0)
        
        self.sock.listen()
        self.socket_list = [self.sock]
        self.clients = {}
        self.user_sock_identify = {}
        
        while True:
            r_sockets, _, except_sockets = select.select(sockets_list, [], sockets_list)
            for notified_socket in r_sockets:
                if notified_socket == self.sock:
                    client_socket, client_address = self.sock.accept()
                    user = receive_message(client_socket)
                    if user is False:
                        continue
                    self.socket_list.append(client_socket)
                    self.clients[client_socket] = user
                    self.user_sock_identify[user["data"].decode("utf-8")] = client_socket
                    print('Accepted new connection from {}:{}, username: {}'.format(*client_address, user['data'].decode('utf-8')))
                else:
                    message = receive_request(notified_socket)
                    if message is False:
                        print('Closed connection from: {}'.format(clients[notified_socket]['data'].decode('utf-8')))
                        self.sockets_list.remove(notified_socket)
                        del self.clients[notified_socket]
                        continue
                    user = self.clients[notified_socket]
                    end_username = message["data"].decode("utf-8")
                    if end_username in self.user_sock_identify.keys():
                        print
                    else:
                        
        
    def receive_request(client_socket):
        try:
            message_header = client_socket.recv(HEAD_LEN)
            if not len(message_header):
                return False

            message_length = int(message_header.decode('utf-8').strip())
            return {'header':message_header, 'data': client_socket.recv(message_length)}
        except:
            return False
    
