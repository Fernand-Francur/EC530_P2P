import sys
import socket
import types
import select
import pickle
import _thread
import pdb

PORT = 60001
HEAD_LEN = 10
REQ_LEN = 10

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
            try:
                r_sockets, _, except_sockets = select.select(self.socket_list, [], self.socket_list)
                for notified_socket in r_sockets:
                    if notified_socket == self.sock:
                        client_socket, client_address = self.sock.accept()
                        user = self.receive_request(client_socket)
                        if user is False:
                            continue
                        if user["request"] != "LOGIN":
                            print("Connection without LOGIN triggered and terminated")
                            continue
                        self.socket_list.append(client_socket)
                        self.clients[client_socket] = user
                        self.user_sock_identify[user["data"].decode("utf-8")] = client_address
                        print('Accepted new connection from {}:{}, username: {}'.format(*client_address, user['data'].decode('utf-8')))
                        print(client_socket.getpeername())
                    else:
                        message = self.receive_request(notified_socket)
                        if message is False:
                            print('Closed connection from: {}'.format(self.clients[notified_socket]['data'].decode('utf-8')))
                            self.socket_list.remove(notified_socket)
                            del self.clients[notified_socket]
                            continue
                        user = self.clients[notified_socket]
                        if message["request"] == "CHAT_REQ":
                            end_username = message["data"].decode("utf-8")
                            
                            if end_username in self.user_sock_identify.keys():
                                request = (f'{"CHAT_REP":<{REQ_LEN}}')
                                msg = pickle.dumps(self.user_sock_identify[end_username])
                                msg = ((f"{len(msg):<{HEAD_LEN}}")+request).encode("utf-8")+msg
                                notified_socket.send(msg)
                            else:
                                request = (f'{"CHAT_REPB":<{REQ_LEN}}')
                                msg = "User " + end_username + " does not exist"
                                msg = (f"{len(msg):<{HEAD_LEN}}")+request+msg
                                notified_socket.send(msg.encode("utf-8"))
                        else:
                            print("NOT YET IMPLEMENTED")
            except KeyboardInterrupt:
                #self.sock.shutdown()
                self.sock.close()
                print("Server has been closed")
                break
                        
                        
        
    def receive_request(self,client_socket):
        try:
            message_header = client_socket.recv(HEAD_LEN)
            if not len(message_header):
                return False
            message_length = int(message_header.decode('utf-8').strip())
            request = client_socket.recv(REQ_LEN).decode('utf-8').strip()
            if not len(request):
                return False
            return {'header':message_header,'request':request, 'data': client_socket.recv(message_length)}
        except:
            return False
    

def main():
    discoveryserver = discover()


if __name__ == "__main__":
    main()
