"""CD Chat client program"""
import logging
import sys
import socket
import selectors
import fcntl
import os

from .protocol import CDProto, CDProtoBadFormat

logging.basicConfig(filename=f"{sys.argv[0]}.log", level=logging.DEBUG)


class Client:
    """Chat Client process."""

    def __init__(self, name: str = "Foo"):
        """Initializes chat client."""
        self.name = name
        self.clientsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.addr = ("localhost", 12345)
        self.channel = None
        self.sel = selectors.DefaultSelector()
        
    

    def connect(self):
        """Connect to chat server and setup stdin flags."""
        
        self.clientsock.connect(self.addr)
        self.sel.register(self.clientsock, selectors.EVENT_READ, self.receive_msg)
        print(f"[{self.name}] connecting to server {self.addr[0]}:{self.addr[1]}")
        register_server = CDProto.register(self.name)
        CDProto.send_msg(self.clientsock, register_server)
    
    

    def receive_msg(self, conn, mask):

        pass_msg = CDProto.recv_msg(self.clientsock)
        
        if pass_msg.command == "message":
            logging.debug('received "%s', pass_msg.message)
        
        print(pass_msg.message)

    def got_keyboard_data(self,stdin, mask):
        
        input_msg = stdin.read().replace("\n", "")
        w = input_msg.split(" ")

        if(w[0] == "exit"):
            self.sel.unregister(self.clientsock)
            self.clientsock.close()
            sys.exit(f"Bye {self.name}!")

        elif(w[0] == "/join" and len(w) == 2):
            self.channel = w[1]
            print(f"{self.name} joined {self.channel}")
            CDProto.send_msg(self.clientsock, CDProto.join(self.channel))

        else:
            msg = CDProto.message(input_msg, self.channel)
            CDProto.send_msg(self.clientsock, msg)

    def loop(self):
        """Loop indefinetely."""
        try:
            origin_file = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
            fcntl.fcntl(sys.stdin, fcntl.F_SETFL, origin_file | os.O_NONBLOCK)
            
            self.sel.register(sys.stdin, selectors.EVENT_READ, self.got_keyboard_data)
            
            while True:
                sys.stdout.write(">> ")
                sys.stdout.flush()

                for key, mask in self.sel.select():
                    callback = key.data
                    callback(key.fileobj, mask)

        except KeyboardInterrupt:
            print("")
            sys.exit(0)
