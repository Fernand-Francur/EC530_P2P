import sys
import socket
import types
import select
import pickle
import pdb
import logging
import sqlite3

HEAD_LEN = 10
REQ_LEN = 10
USER_LEN = 63

logging.basicConfig(
    filename='Debug,log',
    encoding='utf-8',
    level=logging.WARNING)

class Peer2PeerClient:
    def __init__(self, username, port, ip=None, discover_host=None, discover_port=None):
        """
        We have a hardcoded discovery server that these currently connect to which is 
        my local host. To work between computers, a discovery server id must be specified.
        This can be done by accessing a online database in the future, but for this
        implementation, we focus on specifically the peer to peer side and offline
        protocols. Online database is not implemented so server must be entered
        manually at this time. 

        IP for client can also be specified, but only important inputs are username and port
        """
        if discover_host is None:
            self.discover_host = socket.gethostname()
        else:
            self.discover_host = discover_host
        if discover_port is None:
            self.discover_port = 60001
        else:
            self.discover_port = discover_port

        if ip is None:
            self.ip = socket.gethostname()
        else:
            self.ip = ip
        self.port = port
        self.username = username
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        self.sock.bind((self.ip,self.port))
        self.sock.setblocking(False)
        self.socket_list = [self.sock]

        self.clients = {}
        self.user_sock = {}

        """
        The client automatically connects to discovery socket
        """
        try:
            self.discovery_socket = socket.create_connection((self.discover_host,self.discover_port))
        except socket.error:
            logging.error("Connection with discovery server could not be established:\n")
            sys.exit()
            
            
        address = pickle.dumps((self.ip,self.port))
        my_user = f'{self.username:<{USER_LEN}}'.encode('utf-8')
        username_header = f"{len(address):<{HEAD_LEN}}".encode('utf-8')
        request = (f'{"LOGIN":<{REQ_LEN}}').encode('utf-8')
        self.sock.listen()
        sent = self.discovery_socket.send(username_header + request + my_user + address)
        if sent == 0:
            logging.error("Could not communicate with discovery server")
            sys.exit()
        self.socket_list.append(self.discovery_socket)
        self.socket_list.append(sys.stdin)
        self.database = self.username + "_chat.db"
        self.con = sqlite3.connect(self.database)
        self.cur = self.con.cursor()
        
        
        self.run()
        
    def run(self):
        print("P2P Session Started for User " + self.username)
        print("Type the following options for actions")
        print("To start new chat with another user: REQUEST *name-of-user-you-want-to-chat-with*")
        print("Once chat is started, type messages: CHAT *name* *message*")
        print("To close application, type: LOGOUT")
        while True:
            try:
                rList, wList, error_list = select.select(self.socket_list,[],self.socket_list)
                for sock in rList:

                    # ACCEPTING CONNECTIONS
                    if sock == self.sock:
                        chat_socket, chat_address = self.sock.accept()
                        user = self.receive_request(chat_socket)
                        if user is False:
                            continue
                        if user["request"] == "CHAT_REQ":
                            self.socket_list.append(chat_socket)
                            self.clients[chat_socket] = user
                            self.user_sock[user["data"].decode("utf-8")] = chat_socket
                            print('Accepted new connection from {}:{}, username: {}'.format(*chat_address, user['data'].decode('utf-8')))
                            self.cur.execute("CREATE TABLE if not exists " +  user['data'].decode('utf-8') + " (msg TEXT NOT NULL, incoming INTEGER ,sent INTEGER)")
                            self.con.commit()
                        else:
                            print("NOT IMPLEMENTED YET")


                    # IF USER PUTS IN INPUT
                    elif sock == sys.stdin:
                        msg=sys.stdin.readline()
                        if msg.strip() == "LOGOUT":
                            self.sock.close()
                            print("Server has been closed")
                            self.con.close()
                            quit()
                        m = msg.split(" ",2)


                        # IF USER WANTS TO SEND MESSAGE
                        if m[0].strip() == "CHAT":
                            if len(m) == 3:
                                username = m[1].strip()
                                if username in self.user_sock.keys():
                                    msg = m[2].strip().encode("utf-8")
                                    if self.user_sock[username] == None:
                                        print("Connection to user: " +username+" has been closed")
                                        print("Messages will be delivered on reconnect")
                                        self.cur.execute("INSERT INTO "+username+" VALUES (?,?,?)",(msg,0,0))
                                        self.con.commit()
                                        self.user_sock[username] = 1
                                        request = (f'{"PENDING":<{REQ_LEN}}').encode('utf-8')
                                        msg = username.encode('utf-8')
                                        header = (f"{len(msg):<{HEAD_LEN}}").encode("utf-8")
                                        print("Sending PENDING to discovery")
                                        sent = self.discovery_socket.send(header+request+msg)
                                        
                                        if sent == 0:
                                            logging.error("ERROR: Message was not sent")
                                            continue

                                        
                                    elif self.user_sock[username] == 1:
                                        self.cur.execute("INSERT INTO "+username+" VALUES (?,?,?)",(msg,0,0))
                                        self.con.commit()
                                    else:
                                        new_sock = self.user_sock[username]
                                        request = (f'{"CHAT_MESS":<{REQ_LEN}}').encode('utf-8')
                                        header = (f"{len(msg):<{HEAD_LEN}}").encode("utf-8")
                                        sent = new_sock.send(header+request+msg)
                                        if sent == 0:
                                            logging.error("ERROR: Message was not sent")
                                        else:
                                            self.cur.execute("INSERT INTO "+username+" VALUES (?,?,?)",(msg,0,1))
                                            self.con.commit()
                                else:
                                    logging.info("No chat with user "+m[1].strip()+" found.")
                                    print("No chat with user "+m[1].strip()+" found.")

                            else:
                                print("ERROR: Message was not sent")
                                logging.info("User input error: ",m)

                        # USER WANTS TO REQUEST NEW CHAT
                        elif m[0].strip() == "REQUEST":
                            if len(m) == 2:
                                if m[1].strip() in self.user_sock.keys():
                                    print("Chat already has been started with user: "+ m[1].strip())
                                    logging.info("Chat already has been started with user: "+ m[1].strip())
                                else:
                                    request = (f'{"CHAT_REQ":<{REQ_LEN}}').encode('utf-8')
                                    msg = m[1].strip().encode("utf-8")
                                    header = (f"{len(msg):<{HEAD_LEN}}").encode("utf-8")
                                    sent = self.discovery_socket.send(header+request+msg)
                                    if sent == 0:
                                        logging.error("ERROR: Message was not sent")
                            else:
                                print("ERROR: Message was not sent")
                                logging.info("User input error: ",m)
                        else:
                            print("Undefined input: ",m)
                            logging.info("Undefined input: ",m)

                            
                    # MESSAGE RECEIVED FROM NEITHER STDIN NOR FROM NEW CONNECTION        
                    else:
                        message = self.receive_request(sock)
                        if message is False:
                            print('Closed connection from: {}'.format(self.clients[sock]['data'].decode('utf-8')))
                            self.socket_list.remove(sock)
                            self.user_sock[self.clients[sock]['data'].decode('utf-8')] = None
                            del self.clients[sock]
                            continue
                        if message["request"] == "CHAT_MESS":
                            try:
                                user = self.clients[sock]
                            except KeyError:
                                logging.info("User not found in chat log")
                                print("User not found in chat log")
                                continue
                            text_message = message["data"].decode("utf-8")
                            username = user["data"].decode("utf-8")
                            self.cur.execute("INSERT INTO "+username+" VALUES (?,?,?)",(text_message,1,1))
                            self.con.commit()
                            print(username + ": " + text_message)

                        # REPLY FROM DISCOVERY SERVER    
                        elif message["request"] == "CHAT_REP":
                            new_sock_add = pickle.loads(message["data"])
                            print(new_sock_add)
                            new_sock = socket.create_connection(new_sock_add)
                            request = (f'{"CHAT_REQ":<{REQ_LEN}}').encode('utf-8')
                            msg = self.username.encode("utf-8")
                            header = (f"{len(msg):<{HEAD_LEN}}").encode("utf-8")
                            sent = new_sock.send(header+request+msg)
                            username = message["user"]
                            if sent == 0:
                                logging.error("ERROR: Message was not sent")
                            else:
                                self.clients[new_sock] = {"data": username.encode("utf-8")}
                                self.socket_list.append(new_sock)
                                if username in self.user_sock:
                                    if self.user_sock[username] == 1:
                                        self.send_buffer(username,new_sock)
                                else:
                                    self.cur.execute("CREATE TABLE if not exists " +username+ " (msg TEXT NOT NULL, incoming INTEGER ,sent INTEGER)")
                                    self.con.commit()
                                self.user_sock[username] = new_sock
                            
                        elif message["request"] == "CHAT_REPB":
                            logging.info("User not found on discovery server")
                            print("User not found on discovery server")
                            continue
                        else:
                            print("NOT YET IMPLEMENTED")
            except KeyboardInterrupt:
                #self.sock.shutdown()
                self.sock.close()
                print("Server has been closed")
                self.con.close()
                break

    def send_request(self, username, msg):
        try:
            end_socket = self.user_sock[username]
        except:
            return False
        msg_header = f"{len(msg):<{HEAD_LEN}}".encode('utf-8')
        bytes_sent = end_socket.send(msg_header + msg)
        if bytes_sent < (HEAD_LEN + len(msg)):
            return False
        else:
            return True
                
    def receive_request(self,client_socket):
        try:
            message_header = client_socket.recv(HEAD_LEN)
            if not len(message_header):
                return False
            message_length = int(message_header.decode('utf-8').strip())
            request = client_socket.recv(REQ_LEN).decode('utf-8').strip()
            if not len(request):
                return False
            if request == "CHAT_REP":
                user_name = client_socket.recv(USER_LEN).decode('utf-8').strip()
                if not len(user_name):
                    return False
                return {'header':message_header,'request':request, 'user': user_name,'data': client_socket.recv(message_length)}
            return {'header':message_header,'request':request, 'data': client_socket.recv(message_length)}
        except:
            return False

    def send_buffer(self,username,new_sock):
        
        self.cur.execute("SELECT msg FROM "+username+" WHERE sent=0")
        c = self.cur.fetchall()
        print("User "+username+" has come online")
        #print(c)
        for message in c:
            msg2send = message[0]
            request = (f'{"CHAT_MESS":<{REQ_LEN}}').encode('utf-8')
            header = (f"{len(msg2send):<{HEAD_LEN}}").encode("utf-8")
            sent = new_sock.send(header+request+msg2send)
            if sent == 0:
                logging.error("ERROR: Message was not sent")
            else:
                self.cur.execute("UPDATE "+username+" SET sent=1 WHERE msg=?",(msg2send,))
                self.con.commit()


def main():
    if len(sys.argv) == 3:
        username = sys.argv[1]
        port = int(sys.argv[2])
        client = Peer2PeerClient(username, port)
    else:
        print("Incorrect input")


if __name__ == "__main__":
    main()



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
