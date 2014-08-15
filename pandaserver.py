#Panda board as server
import sys
import socket
import select
from pymouse import PyMouse
import threading


image_width = 640.0
image_height = 480.0

calibration_success = False

class Server(threading.Thread):

    def __init__(self, host, port):
        threading.Thread.__init__(self)
        self.host = str(host)
        self.port = int(port)
        self.thread_list = []
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
        except socket.error as error:
            print error

    def run(self):
        inputs = [self.server_socket, sys.stdin]
        run = True
        while run:
            input_ready, output_ready, except_ready = select.select(inputs, [], [])
            for s in input_ready:
                if s == self.server_socket:
                    handle = ClientThread(self.server_socket.accept())
                    self.thread_list.append(handle)
                    handle.start()

                elif s == sys.stdin:
                    run = False
                    sys.exit(1)

        for handle in self.thread_list:
            handle.join()
        self.server_socket.close()


class ClientThread(threading.Thread):
    def __init__(self, (client, address)):
        threading.Thread.__init__(self)
        self.client = client
        self.address = address
        self.data = None

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

    def parser(self, data, m):
        width = m.screen_size()[0]
        height = m.screen_size()[1]
        factorx = width/image_width
        factory = height/image_height
        split = data.split(';')
        x = int(split[1])
        y = int(split[2])
        if x != 0 and y != 0:
            scaledx = x * factorx
            scaledy = y * factory
            if split[0] == 'm':
                m.move(scaledx, scaledy)
            elif split[0] == 'md':
                m.press(scaledx, scaledy)
            elif split[0] == 'mr':
                m.release(scaledx, scaledy)

    def calibrate(self, client, root):
        client.send('start' + '\0')
        running = True
        inputs = [client, sys.stdin]
        global calibration_success
        while running:
            input_ready, output_ready, except_ready = select.select(inputs, [], [])
            for s in input_ready:
                if s == client:
                    data = self.receiver()
                    if 'done' in self.data:
                        calibration_success = True
                        print "success"
                        root.destroy()
                        return
                    elif 'failed' in self.data:
                        calibration_success = False
                        print "failed"
                        root.destroy()
                        return

    def splash_screen(self, client):
        import Tkinter as t
        import splash as s
        root = t.Tk()
        sp = s.SplashScreen(root)
        sp.config(bg="#fff")
        root.after(1000, self.calibrate, client, root)
        root.mainloop()
        if calibration_success:
            client.send('done' + '\0')
        else:
            client.send('failed' + '\0')


    def client_handler(self):
        inputs = [self.client, sys.stdin]
        running = True
        m = PyMouse()
        while running:
            input_ready, output_ready, except_ready = select.select(inputs, [], [])
            for s in input_ready:
                if s == self.client:
                    errors = self.receiver()
                    if not errors:
                        if 'splash' in self.data:
                            self.splash_screen(self.client)
                        else:
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

    def run(self):
        flag = self.client_handler()
        if flag:
            return True

try:
    server = Server("0.0.0.0", 9999)
    flag = server.start()
    if flag:
        server.exit()
except socket.error as error:
    print error
    sys.exit(1)
