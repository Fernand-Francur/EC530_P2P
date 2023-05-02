import sys
import socket
import types
import select
import pickle
import _thread
import pdb
import sqlite3

PORT = 60001
HEAD_LEN = 10
REQ_LEN = 10
USER_LEN = 63


"""
Discovery server to be used with clients holds connection and user data.
Is responsible for only providing clients with information to create connections, but does
not hold any message information. Works independently of clients. Automatically starts
on localhost and preset port, but can be specified in start at runtime
"""
class discover:
    def __init__(self, ip=None, port=None):

        # Socket Set up
        self.discoverDict = {}
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock

        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)

        if ip == None:   
            self.host = socket.gethostname()
        else:
            self.host = ip

        if host == None:
            self.port = port
        else:
            self.port = PORT
        self.sock.bind((self.host,self.port))
        print("Discover server has started")
        print("Awaiting clients")
        self.sock.setblocking(0)
        
        self.sock.listen()

        # Setting up variables and data structures
        self.socket_list = [self.sock]
        self.clients = {}
        self.user_sock_identify = {}
        self.reverse_clients = {}
        self.pending_list = {}
        self.connections = {}

        # Setting up database for connections and users
        self.database = "connections_database.db"
        self.con = sqlite3.connect(self.database)
        self.cur = self.con.cursor()

        # Retrieving data on connections from databases
        self.cur.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name")
        tables = self.cur.fetchall()
        for username in tables:
            self.connections[username[0]] = []
            self.user_sock_identify[username[0]] = None
            self.cur.execute("SELECT user FROM "+username[0])
            users = self.cur.fetchall()
            for name in users:
                self.connections[username[0]].append(name[0])
            try:
                print("NOT IMPLEMENTED RECONNECT")
                
            except:
                print("User, "+username+" is offline")

        # Starts socket queue which handles all socket communication
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
                        username = user['user']
                        if username in self.connections.keys():
                            request = (f'{"CHAT_REP":<{REQ_LEN}}')
                            for connect_user in self.connections[username]:
                                if self.user_sock_identify[connect_user] != None:
                                    msg = pickle.dumps(self.user_sock_identify[connect_user])
                                    user_name = (f'{connect_user:<{USER_LEN}}')
                                    msg = ((f"{len(msg):<{HEAD_LEN}}")+request+user_name).encode("utf-8")+msg
                                    sent = client_socket.send(msg)
                                    if sent == 0:
                                        logging.error("ERROR: Could not send connection")
                        else:
                            self.connections[username] = []
                            self.cur.execute("CREATE TABLE if not exists "+username+" (user TEXT NOT NULL)")
                            self.con.commit()
                                
                        if user['user'] in self.pending_list.keys():
                            rm_pending = []
                            request = (f'{"CHAT_REP":<{REQ_LEN}}')
                            print(self.user_sock_identify[username])
                            msg = pickle.dumps(self.user_sock_identify[username])
                            user_name = (f'{username:<{USER_LEN}}')
                            msg = ((f"{len(msg):<{HEAD_LEN}}")+request+user_name).encode("utf-8")+msg
                            for rec in self.pending_list[user['user']]:
                                if self.user_sock_identify[rec] != None:
                                    new_sock = self.reverse_clients[rec]
                                    sent = new_sock.send(msg)
                                    if sent == 0:
                                        logging.error("ERROR: Message was not sent")
                                    else:
                                        rm_pending.append(rec)
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
                                self.connections[end_username].append(user['user'])
                                self.connections[user['user']].append(end_username)
                                notified_socket.send(msg)
                                self.cur.execute("INSERT INTO "+end_username+" VALUES (?)",(user['user'],))
                                self.cur.execute("INSERT INTO "+user['user']+" VALUES (?)",(end_username,))
                                self.con.commit()
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
                self.sock.close()
                self.con.close()
                print("Server has been closed")
                break
                                
    """
    Interprets the received packets from discovery server and other clients and outputs
    a general format usable by the rest of the code
    """
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
