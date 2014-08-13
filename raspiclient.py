#raspberry pi as client
import io
import cv2
import sys
import time
import laser
import socket
import picamera
import numpy as np
import picamera.array

THRESHOLD = 60


def laser_position(hsv, factor):
    x = y = w = h = 0
    # gray = cv2.cvtColor(, cv2.COLOR_BGR2GRAY)
    print "after conversion"
    lower_red = np.array([150, 30, 210], dtype=np.uint8)
    upper_red = np.array([179, 255, 255], dtype=np.uint8)
    mask = cv2.inRange(hsv, lower_red, upper_red)
    res = cv2.bitwise_and(hsv, hsv, mask=mask)
    cv2.imshow("res", res)
    cv2.waitKey(1000/24)
    # ret, thresh = cv2.threshold(gray, factor, 255, cv2.THRESH_BINARY)
    # print "after threshold"
    # contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # print "after contour"
    # if len(contours) > 0:
    #     print "greater than"
    #     laser_state = 1
    #     cnt = contours[0]
    #     x, y, w, h = cv2.boundingRect(cnt)
    # else:
    #     print "less than"
    #     laser_state = 0
    #     x = y = w = h = 0
    # return x, y, w, h, laser_state


def laser_main(client_socket):
    with picamera.PiCamera() as camera:
        camera.resolution = (640, 480)
        camera.framerate = 24
        time.sleep(0.1)
        laser_object = laser.Laser(client_socket)
        while True:
            with picamera.array.PiRGBArray(camera) as stream:
                camera.capture(stream, format='bgr', use_video_port=True)
                bgr = stream.array
                hsv = cv2.cvtColor(stream.array, cv2.COLOR_BGR2HSV)
                h, s, v = cv2.split(hsv)
                average = np.average(v)
                if average > THRESHOLD:
                    print "correction", average
                    temporary = camera.exposure_compensation
                    temporary -= int((average - THRESHOLD)/10)
                    try:
                        if temporary < -25:
                            camera.exposure_compensation = -25
                        elif temporary > 25:
                            camera.exposure_compensation = 25
                        else:
                            camera.exposure_compensation = temporary
                    except picamera.PiCameraValueError:
                        print "error"
                laser_position(hsv, 200)
                # x, y, w, h, laser_state = laser_position(hsv, 200)
                # print "x\'s", x, y, w, h, laser_state
                # laser_object.container(x, y, w, h, laser_state)


class Client(object):
    def __init__(self, host="192.168.1.1", port=9000):
        self.host = str(host)
        self.port = int(port)
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.client_socket.connect((self.host, self.port))
        except socket.error as error:
            print error
            sys.exit(1)

    def handle(self):
        laser_main(self.client_socket)

if __name__ == "__main__":
    try:
        pi = Client()
        pi.handle()
    except socket.error as error:
        print error
        sys.exit(1)