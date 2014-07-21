#raspberry pi as client
import io
import cv2
import sys
import laser
import socket
import numpy as np
#this needs to be made dynamic too
AIV_threshold = 60
# ROI_FACTOR = 25
JERKS = 2


#class that analyzes motions of laser
class Motion(object):
    """This class has methods to find laser spot and send it to container class for appropriate motions. The client
    makes this object and calls on the method lasermain() with its client socket as parameter.
    """
    def __init__(self):
        # current working frame
        self.frame = None
        # # for roi
        # self.boundx = 0
        # self.boundy = 0
        # self.boundw = 640
        # self.boundh = 480
        #states
        self.previoustate = 0
        #previous x, y, w, h
        self.x = 0
        self.y = 0
        self.w = 0
        self.h = 0

    def increasedecreaseroi(self, x, y, w, h):
        """This function is used to narrow the search window once laser has been spotted to its immediate neighbourhood
            comprising of pixels' size ROI_FACTOR.
            Args: int
                x, y, w, h: coordinates of laser spot
            Yields: int
                The width and height of the laser spot is increased by the ROI_FACTOR. The value of x is adjusted
                by decreasing half of the width, and so is the y value but decreased by half of the height. If the
                values of x and y gets less than 0, it is restrained to value 0
        """
        w *= ROI_FACTOR
        h *= ROI_FACTOR
        x -= w / 2
        if x < 0:
            x = 0
        y -= h / 2
        if y < 0:
            y = 0
        return x, y, w, h

    def removejerks(self, x, y, w, h):
        """This function discards the small motions of the lasers caused by hand movements.
            Args: int
                x, y, w, h: coordinates of laser spot
            Yields: int
                if the new coordinates are larger than old coordinates by JERKS(threshold), these new coordinates are
                    used,
                else the old coordinates is used
        """
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

    def laserposition(self, factor):
        """The function calculates the coordinates of the laser spot. It thresholds the image based on its white pixels
            only, in the range 200-255. From the thresholded image, contour is found out distinctly, which is the laser
            spot. This laser spot is approximated via a bounding rectangle, thereby giving us coordinates x, y, w,h
            Args: numpy array/cv2 object
                Class variable frame
            Yields: int
                x, y, w, h: coordinates of laser spot

            Here, when no laser spot is found, whole frame is scanned but once laser spot has been found, in the next
            detection phase, the frame is sliced up using the previous laser spot boundaries, given by increasedecrease-
            roi
        """
        frame = self.frame
        x = y = w = h = 0
        #roi
        # frame = frame[self.boundy: self.boundy + self.boundh, self.boundx: self.boundx + self.boundw]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        #thresholding has been done only for bright white
        ret, thresh = cv2.threshold(gray, factor, 255, cv2.THRESH_BINARY)
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) > 0:
            laser_state = 1
            cnt = contours[0]
            x, y, w, h = cv2.boundingRect(cnt)
            # #for roi
            # x += self.boundx
            # y += self.boundy
            # self.boundx, self.boundy, self.boundw, self.boundh = self.increasedecreaseroi(x, y, w, h)
        else:
            laser_state = 0
            #for roi
            # self.boundx = 0
            # self.boundy = 0
            # self.boundw = 640
            # self.boundh = 480
        return x, y, w, h, laser_state

    def show(self, data, delay):
        cv2.imshow("images", data)
        cv2.waitKey(delay)

    def pcmain(self, clientsocket):
        cap = cv2.VideoCapture(0)
        laserobject = laser.Laser(clientsocket)
        while True:
            ret, self.frame = cap.read()
            x, y, w, h, state = self.laserposition(150)
            laserobject.container(x, y, w, h, state)


    def lasermain(self, clientsocket):
        """This function opens the camera, sets the framerate, corrects the exposure, calls laserposition() method to
        get the coordinates of laser spot and passed to removejerks() method. And then sent to container class Laser()
        Args: clientsocket
            This socket arg is passed to the container class Laser which interprets the laser coordinates and motions
            and sends to the server.
        """
        import picamera
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
                x, y, w, h, laserstate = self.laserposition(200)
                print "x\'s", x, y, w, h, laserstate
                # x, y, w, h = self.removejerks(x, y, w, h)
                laserobject.container(x, y, w, h, laserstate)


class Client(object):
    """This class is a client class for raspberry pi to connect to the server running on the panda board. Currently the
    server is being run on a local machine which is providing the raspberry pi with an IP via the ethernet. The local
    machine's ethernet IP is set to 192.168.0.1. Since the server has its socket opened at 192.168.0.1 and listening on
    the port 9999, we have created a client socket for the same host and port.

    The __init__ method connects to the server and sets connected variable to True. After which, the handle method is
    run, which creates Motion class object. And this object calls the method lasermain() and passed the client socket
    to it.
    """
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
            try:
                Motion().lasermain(self.clientsocket)
            except ImportError as error:
                try:
                    Motion().pcmain(self.clientsocket)
                except cv2.error:
                    print "error"

if __name__ == "__main__":
    try:
        pi = Client()
        pi.handle()
    except socket.error as error:
        print error
        sys.exit(1)

