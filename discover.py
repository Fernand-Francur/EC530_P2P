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
USER_LEN = 63

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
        self.reverse_clients = {}
        self.pending_list = {}
        
        
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
                        
                        self.user_sock_identify[user["user"]] = pickle.loads(user["data"])
                        self.reverse_clients[user["user"]] = client_socket
                        print('Accepted new connection from {}:{}, username: {}'.format(*self.user_sock_identify[user["user"]], user['user']))
                        if user['user'] in self.pending_list.keys():
                            rm_pending = []
                            #print("Enters if "+user['user'])
                            for rec in self.pending_list[user['user']]:
                                #print("Enters for")
                                if self.user_sock_identify[rec] != None:
                                    #print("Asked by "+rec)
                                    request = (f'{"CHAT_REP":<{REQ_LEN}}')
                                    username = user['user']
                                    print(self.user_sock_identify[username])
                                    msg = pickle.dumps(self.user_sock_identify[username])
                                    user_name = (f'{username:<{USER_LEN}}')
                                    msg = ((f"{len(msg):<{HEAD_LEN}}")+request+user_name).encode("utf-8")+msg
                                    new_sock = self.reverse_clients[rec]
                                    #print(new_sock)
                                    #print(self.clients[new_sock])
                                    sent = new_sock.send(msg)
                                    if sent == 0:
                                        logging.error("ERROR: Message was not sent")
                                    else:
                                        rm_pending.append(rec)
                                else:
                                    print("Not yet implemented")
                            for rm_user in rm_pending:
                                self.pending_list[user['user']].remove(rm_user)
                                

                        
                    else:
                        message = self.receive_request(notified_socket)
                        if message is False:
                            print('Closed connection from: {}'.format(self.clients[notified_socket]['user']))
                            self.socket_list.remove(notified_socket)
                            self.user_sock_identify[self.clients[notified_socket]['user']] = None
                            self.reverse_clients[self.clients[notified_socket]['user']] = None
                            del self.clients[notified_socket]
                            continue
                        user = self.clients[notified_socket]
                        if message["request"] == "CHAT_REQ":
                            end_username = message["data"].decode("utf-8")
                            
                            if end_username in self.user_sock_identify.keys():
                                request = (f'{"CHAT_REP":<{REQ_LEN}}')
                                msg = pickle.dumps(self.user_sock_identify[end_username])
                                username = (f'{end_username:<{USER_LEN}}')
                                msg = ((f"{len(msg):<{HEAD_LEN}}")+request+username).encode("utf-8")+msg
                                notified_socket.send(msg)
                            else:
                                request = (f'{"CHAT_REPB":<{REQ_LEN}}')
                                msg = "User " + end_username + " does not exist"
                                msg = (f"{len(msg):<{HEAD_LEN}}")+request+msg
                                notified_socket.send(msg.encode("utf-8"))
                        elif message["request"] == "PENDING":
                            
                            curr_user = self.clients[notified_socket]['user']
                            end_user = message["data"].decode("utf-8")
                            print("Received pending from "+curr_user+" to "+end_user)
                            if end_user not in self.pending_list.keys():
                                self.pending_list[end_user] = []
                            self.pending_list[end_user].append(curr_user)
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
            if request == "LOGIN":
                user_name = client_socket.recv(USER_LEN).decode('utf-8').strip()
                if not len(user_name):
                    return False
                return {'header':message_header,'request':request, 'user': user_name,'data': client_socket.recv(message_length)}
            return {'header':message_header,'request':request, 'data': client_socket.recv(message_length)}
        except:
            return False
    

def main():
    discoveryserver = discover()


if __name__ == "__main__":
    main()
