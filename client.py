import sys
import socket
import types
import select
import pdb 

HEAD_LEN = 10
REQ_LEN = 10

class Peer2PeerClient:
    def __init__(self, username, port, ip=None, discover_host=None, discover_port=None):
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

        self.chatter_list = []
        self.clients = {}
        self.user_sock = {}
        
        self.discovery_socket = socket.create_connection((self.discover_host,self.discover_port))
        
        my_user = self.username.encode('utf-8')
        username_header = f"{len(my_user):<{HEAD_LEN}}".encode('utf-8')
        request = (f'{"LOGIN":<{REQ_LEN}}').encode('utf-8')
        self.discovery_socket.send(username_header + request + my_user)
        self.socket_list.append(self.discovery_socket)
        self.socket_list.append(sys.stdin)
        self.sock.listen()
        self.run()
        
    def run(self):
        while True:
            try:
                rList, wList, error_list = select.select(self.socket_list,[],self.socket_list)
                for sock in rList:
                    if sock == self.sock:
                        chat_socket, chat_address = self.sock.accept()
                        user = self.receive_request(chat_socket)
                        if user is False:
                            continue
                        if user["request"] == "CHAT_REQ":
                            self.socket_list.append(chat_socket)
                            self.chatter_list.append(chat_socket)
                            self.clients[chat_socket] = user
                            self.user_sock[user["data"].decode("utf-8")] = chat_socket
                            print('Accepted new connection from {}:{}, username: {}'.format(*chat_address, user['data'].decode('utf-8')))
                        else:
                            print("NOT IMPLEMENTED YET")
                    elif sock == sys.stdin:
                        msg=sys.stdin.readline()
                        print(msg)
                        
                    else:
                        message = self.receive_request(sock)
                        if message is False:
                            print('Closed connection from: {}'.format(self.clients[sock]['data'].decode('utf-8')))
                            self.socket_list.remove(sock)
                            self.chatter_list.append(sock)
                            del self.clients[sock]
                            continue
                        user = self.clients[sock]
                        if message["request"] == "CHAT_MESS":
                            text_message = message["data"].decode("utf-8")
                            username = user["data"].decode("utf-8")
                            sys.stdout(username + " : " + text_message)
                        else:
                            print("NOT YET IMPLEMENTED")
            except KeyboardInterrupt:
                #self.sock.shutdown()
                self.sock.close()
                print("Server has been closed")
                break

    def listener(self):
        return 0

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
            return {'header':message_header,'request':request, 'data': client_socket.recv(message_length)}
        except:
            return False


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
