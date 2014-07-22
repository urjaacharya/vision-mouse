#Panda board as server
import sys
import socket
import select
from pymouse import PyMouse
import threading

FACTORX = int(1366/640)
FACTORY = int(768/480)


class Server(threading.Thread):

    def __init__(self, host, port):
        threading.Thread.__init__(self)
        self.host = str(host)
        self.port = int(port)
        self.threadlist = []
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
        errors = False
        while not flag:
            try:
                self.data += self.client.recv(1)
                try:
                    if self.data[-1] == '\0':
                        self.data = self.data[:-1]
                        self.data = str(self.data)
                        return errors
                except IndexError as error:
                    print error
                    errors = True
                    return errors
            except socket.error as error:
                print error
                errors = True
                return errors

    # mouse actions parser
    def parser(self, data, m):
        split = data.split(';')
        scalex = int(split[1]) * FACTORX
        scaley = int(split[2]) * FACTORY
        if split[0] == 'm':
            m.move(scalex, scaley)
        elif split[0] == 'md':
	#press not click
            m.press(scalex, scaley)
        elif split[0] == 'mr':
            m.release(scalex, scaley)

    def clienthandler(self):
        inputs = [self.client, sys.stdin]
        running = True
        m = PyMouse()
        while running:
            inputready, outputready, exceptready = select.select(inputs, [], [])
            for s in inputready:
                if s == self.client:
                    errors = self.receiver()
                    if not errors:
                        print "decision ", self.data
                        self.parser(self.data, m)
                    else:
                        running = False
                elif s == sys.stdin:
                    junk = sys.stdin.readline()
                    if junk:
                        running = False
        try:
            self.client.close()
            print "client closing"
        except socket.error as error:
            print error

        return True

    #client.start()
    def run(self):
        flag = self.clienthandler()
        if flag:
            return True

try:
    server = Server("192.168.0.1", 9999)
    flag = server.start()
    if flag:
        server.exit()
except socket.error as error:
    print error
    sys.exit(1)
