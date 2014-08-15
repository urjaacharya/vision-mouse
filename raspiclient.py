#raspberry pi as client
import io
import cv2
import sys
import laser
import socket
import select
import numpy as np
#this needs to be made dynamic too
AIV_threshold = 45
VALUE_THRESHOLD = 200
#ROI_FACTOR = 25
JERKS = 1


cx = cy = cw = ch = 0


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
        global AIV_threshold
        global VALUE_THRESHOLD
        frame = self.frame
        x = y = w = h = 0
        #roi
        # frame = frame[self.boundy: self.boundy + self.boundh, self.boundx: self.boundx + self.boundw]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        #thresholding has been done only for bright white
        ret, thresh = cv2.threshold(gray, factor, 255, cv2.THRESH_BINARY)
        cv2.imshow("thresh", thresh)

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
            x, y, w, h, state = self.laserposition(200)
            laserobject.container(x, y, w, h, state)


    def lasermain(self, clientsocket):
        """This function opens the camera, sets the framerate, corrects the exposure, calls laserposition() method to
        get the coordinates of laser spot and passed to removejerks() method. And then sent to container class Laser()
        Args: clientsocket
            This socket arg is passed to the container class Laser which interprets the laser coordinates and motions
            and sends to the server.
        """
        import time
        import picamera
        import picamera.array

        with picamera.PiCamera() as camera:
            camera.resolution = (640, 480)
            camera.framerate = 24
            time.sleep(0.1)
            laserobject = laser.Laser(clientsocket)
            global AIV_threshold
            global VALUE_THRESHOLD
            while True:
                key = cv2.waitKey(1000 / 24)
                if key is ord('a'):
                    AIV_threshold += 5
                elif key is ord('z'):
                    AIV_threshold -= 5
                elif key is ord('s'):
                    VALUE_THRESHOLD += 5
                elif key is ord('x'):
                    VALUE_THRESHOLD -= 5
                elif key is ord('q'):
                    sys.exit(0)
                print "A", AIV_threshold, "V", VALUE_THRESHOLD

                with picamera.array.PiRGBArray(camera) as stream:
                    camera.capture(stream, format='bgr', use_video_port=True)
                    self.frame = stream.array
                    # cv2.imshow("FRAME", self.frame)
                    # key = cv2.waitKey(1000/24)
                    # if key is ord('a'):
                    #     AIV_threshold += 5
                    # elif key is ord('z'):
                    #     AIV_threshold -= 5
                    hsv = cv2.cvtColor(stream.array, cv2.COLOR_BGR2HSV)
                    h, s, v = cv2.split(hsv)
                    average = int(np.average(v))
                    temporary = camera.exposure_compensation
                    if average > AIV_threshold+10:
                        temporary -= 5 #int((average - AIV_threshold)/10)
                    elif average < AIV_threshold-10:
                        temporary += 5

                    if temporary != camera.exposure_compensation:

                        print "C", camera.exposure_compensation, "T", temporary
                        try:
                            if temporary < -25:
                                camera.exposure_compensation = -25
                            elif temporary > 25:
                                camera.exposure_compensation = 25
                            else:
                                camera.exposure_compensation = temporary
                        except picamera.PiCameraValueError as error:
                            print error
                    else:
                        x, y, w, h, laserstate = self.laserposition(VALUE_THRESHOLD)
                        print "x\'s", x, y, w, h, laserstate
                        x, y, w, h = self.removejerks(x, y, w, h)
                        laserobject.container(x, y, w, h, laserstate)


# def quad_check(x, y, w, h):
#     lst = (x, y, w, h)
#     peri = cv2.arcLength(lst, True)
#     approx = cv2.approxPolyDP(lst, 0.02 * peri, True)
#     if approx.size == 4:
#         return True
#     else:
#         return False


def calibrate():
    import time
    import picamera
    import picamera.array
    global cx, cy, cw, ch

    with picamera.PiCamera() as camera:
        camera.resolution = (640, 480)
        camera.framerate = 24
        time.sleep(0.1)
        with picamera.array.PiRGBArray(camera) as stream:
            camera.capture(stream, format='bgr', use_video_port=True)
            bgr = stream.array
            blur = cv2.medianBlur(bgr, 5)
            gray = cv2.cvtColor(blur, cv2.COLOR_BGR2GRAY)
            ret, thresh = cv2.threshold(gray, 127, 255, 0)
            contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(bgr, contours, -1, (255, 0, 0), 2)
            cv2.imshow('bgr', bgr)
            cv2.waitKey(1000/24)
            areas = [cv2.contourArea(c) for c in contours]
            max_index = np.argmax(areas)
            cnt = contours[max_index]
            cx, cy, cw, ch = cv2.boundingRect(cnt)
            if cx != 0:
            #     status = quad_check(cx, cy, cw, ch)
            #     if status:
                return True
            #     else:
            #         return False
            else:
                return False

value = ''


def receiver(client):
    global value
    data = ''
    errors = False
    while True:
        try:
            data += client.recv(1)
            try:
                if data[-1] == '\0':
                    value = data[:-1]
                    value = str(value)
                    return errors
            except IndexError as error:
                print error
                errors = True
                return errors
        except socket.error:
            print "socket error"
            errors = True
            return errors


def ask_for_splash_screen(client_socket):
    global value
    client_socket.send('splash' + '\0')
    inputs = [client_socket, sys.stdin]
    running = True
    status = False
    while running:
        input_ready, output_ready, except_ready = select.select(inputs, [], [])
        for s in input_ready:
            if s == client_socket:
                errors = receiver(client_socket)
                if not errors:
                    if 'start' in value:
                        status = calibrate()
                        if status:
                            print "done", cx, cy, cw, ch
                            client_socket.send('done' + ';' + str(cx) + ';' + str(cy) + ';' + str(cw) + ';' + str(ch) +\
                                               '\0')
                            return status
                        else:
                            client_socket.send('failed' + '\0')
                            return status
                else:
                    running = False
                    status = False
            elif s == sys.stdin:
                junk = sys.stdin.readline()
                if junk:
                    running = False
    return status


class Client(object):
    """This class is a client class for raspberry pi to connect to the server running on the panda board. Currently the
    server is being run on a local machine which is providing the raspberry pi with an IP via the ethernet. The local
    machine's ethernet IP is set to 192.168.0.1. Since the server has its socket opened at 192.168.0.1 and listening on
    the port 9999, we have created a client socket for the same host and port.

    The __init__ method connects to the server and sets connected variable to True. After which, the handle method is
    run, which creates Motion class object. And this object calls the method lasermain() and passed the client socket
    to it.
    """
    def __init__(self, host="192.168.1.1", port=9999):
        self.host = str(host)
        self.port = int(port)
        self.connected = False
        try:
            self.clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.clientsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.clientsocket.connect((self.host, self.port))
            self.connected = True
        except socket.error:
            print "socket error"
            self.connected = False
            sys.exit(1)

    def handle(self):
        if self.connected:
            #TODO CALIBRATION ON DEMAND BY USER
            status = ask_for_splash_screen(self.clientsocket)
            if not status:
                print "failed to calibrate the screen"
                return
            print "success"
            try:
                #works on raspberry pi
                Motion().lasermain(self.clientsocket)
            except ImportError as error:
                try:
                    #work on pc but no exposure compensation will be done
                    Motion().pcmain(self.clientsocket)
                except cv2.error:
                    print "cv2 error"
                    return

if __name__ == "__main__":
    try:
        pi = Client()
        pi.handle()
    except socket.error as error:
        print error
        sys.exit(1)