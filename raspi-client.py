#raspberry pi as client
import io
import cv2
import sys
import laser
import socket
import picamera
import numpy as np
AIV_threshold = 60
ROI_FACTOR = 25
JERKS = 2


#class that analyses motions of laser
class Motion(object):

    def __init__(self):

        # current working frame
        self.frame = None
        # boundary
        self.boundx = 0
        self.boundy = 0
        self.boundw = 640
        self.boundh = 480
        #states
        self.previoustate = 0
        #previous x, y, w, h
        self.x = 0
        self.y = 0
        self.w = 0
        self.h = 0

    def increasedecreaseroi(self, x, y, w, h):
        w *= ROIFACTOR
        h *= ROIFACTOR
        x -= w / 2
        if x < 0:
            x = 0
        y -= h / 2
        if y < 0:
            y = 0
        return x, y, w, h

    def removejerks(self, x, y, w, h):
        if abs(x - self.x) >= JERKS:
            self.x = x
            # print "x updated", self.x
        if abs(y - self.y) >= JERKS:
            self.y = y
            # print "y updated", self.y
        if abs(w - self.w) >= JERKS:
            self.w = w
            # print "w updated", self.w
        if abs(h - self.h) >= JERKS:
            self.h = h
            # print "h updated", self.h
        return self.x, self.y, self.w, self.h

    def laserposition(self):
        frame = self.frame
        x = y = w = h = 0
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        #thresholding has been done only for bright white
        ret, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) > 0:
            laser_state = 1
            cnt = contours[0]
            x, y, w, h = cv2.boundingRect(cnt)
        else:
            laser_state = 0
        return x, y, w, h, laser_state

    def show(self, data, delay):
        cv2.imshow("images", data)
        cv2.waitKey(delay)

    def lasermain(self, clientsocket):
        with picamera.PiCamera() as camera:
            camera.resolution = (640, 480)
            camera.framerate = 24
            stream = io.BytesIO()
            laserobject = laser.Laser(clientsocket)
            while True:
                camera.capture(stream, format="jpeg", use_video_port=True)
                frame = np.fromstring(stream.getvalue(), dtype=np.uint8)
                stream.seek(0)
                self.frame = cv2.imdecode(frame, 1)
                self.frame = self.frame[self.boundy: self.boundy + self.boundh, self.boundx: self.boundx + self.boundw]
                hsv = cv2.cvtColor(self.frame, cv2.COLOR_BGR2HSV)
                h, s, v = cv2.split(hsv)
                average = np.average(v)
                if average > AIV_threshold:
                    print "correction"
                    temporary = camera.exposure_compensation
                    temporary -= int((average - AIV_threshold)/10)
                    try:
                        if temporary < -25:
                            camera.exposure_compensation = -25
                        elif temporary > 25:
                            camera.exposure_compensation = 25
                        else:
                            camera.exposure_compensation = temporary
                    except picamera.PiCameraValueError as error:
                        print error
                x, y, w, h, laserstate = self.laserposition()
                print "xs", x, y, w, h, laserstate
                x, y, w, h = self.removejerks(x, y, w, h)
                laserobject.container(x, y, w, h, laserstate)


class Client(object):
    def __init__(self, host="192.168.0.1", port=9999):
        self.host = str(host)
        self.port = int(port)
        self.connected = False
        try:
            self.clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.clientsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.clientsocket.connect((self.host, self.port))
            self.connected = True
        except socket.error as error:
            print error
            self.connected = False
            sys.exit(1)

    def handle(self):
        if self.connected:
            Motion().lasermain(self.clientsocket)

try:
    pi = Client()
    pi.handle()
except socket.error as error:
    print error
    sys.exit(1)

