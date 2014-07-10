#Panda board as server
import sys
import json
import socket
import select
import threading


class Server(threading.Thread):
    host = None
    port = None
    threadlist = []

    def __init__(self, host, port):
        threading.Thread.__init__(self)
        self.host = str(host)
        self.port = int(port)
        try:
            self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.serversocket.bind((self.host, self.port))
            self.serversocket.listen(5)

        except socket.error as error:
            print error

    def run(self):
        inputs = [self.serversocket, sys.stdin]
        run = True
        while run:
            inputready, outputready, exceptready = select.select(inputs, [], [])
            for s in inputready:
                if s == self.serversocket:
                    handle = ClientThread(self.serversocket.accept())
                    self.threadlist.append(handle)
                    handle.start()

                elif s == sys.stdin:
                    run = False
                    sys.exit(1)

        for handle in self.threadlist:
            handle.join()
        self.serversocket.close()


class ClientThread(threading.Thread):
    def __init__(self, (client, address)):
        threading.Thread.__init__(self)
        self.client = client
        self.address = address
        self.data = None

    #receive data from the client
    def receiver(self):
        self.data = ''
        flag = False
        errors = False
        while not flag:
            try:
                self.data += self.client.recv(1)
                try:
                    if self.data[-1] == '\0':
                        self.data = self.data[:-1]
                        self.data = str(self.data)
                        flag = False
                        return errors
                except IndexError as error:
                    print error
                    flag = True
                    errors = True
                    return errors
            except socket.error as error:
                print socket.error
                errors = True
                flag = True
                return errors

    def clienthandler(self):
        inputs = [self.client, sys.stdin]
        running = True
        while running:
            inputready, outputready, exceptready = select.select(inputs, [], [])
            for s in inputready:
                if s == self.client:
                    errors = self.receiver()
                    if not errors:
                        print self.data
                    else:
                        running = False
                elif s == sys.stdin:
                    junk = sys.stdin.readline()
                    if junk:
                        running = False
        try:
            self.client.close()
            print "client closing"
            sys.exit(1)
        except socket.error as error:
            print error

    #server.start()
    def run(self):
        self.clienthandler()

try:
    server = Server("192.168.0.1", 9090)
    server.start()
except socket.error as error:
    print error
    sys.exit(1)