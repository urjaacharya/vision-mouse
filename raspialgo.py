import io
import cv2
import csv
import time
import picamera
import numpy as np
import laser


AIV_threshold = 60


# #ROI increment factor
NEARFACTOR = 4

#decision making value for click or drag, in a click at least 7 on/off states are visible
TRANSITIONS = 7

#remove small pixel motions
JERKS = 2


class Motion(object):
    def __init__(self):

        #current working frame
        self.frame = None
        #ROI boundary
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
        #mouse actions
        self.rightclick = False
        self.leftclick = False
        self.dragging = False
        #mouse action coordinates
        self.actionx = 0
        self.actiony = 0

    def gettransformedboundingrect(self, x, y, w, h):
        w *= NEARFACTOR
        h *= NEARFACTOR
        x -= w/2
        if x < 0:
            x = 0
        y -= h/2
        if y < 0:
            y = 0
        return x, y, w, h

    def removejerks(self, x, y, w, h):
        if abs(x - self.x) >= JERKS:
            self.x = x
        if abs(y - self.y) >= JERKS:
            self.y = y
        if abs(w - self.w) >= JERKS:
            self.w = w
        if abs(h - self.h) >= JERKS:
            self.h = h
        return self.x, self.y, self.w, self.h

    def laserposition(self):
        frame = self.frame
        x = y = w = h = 0
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        ret, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) > 0:
            laser_state = 1
            cnt = contours[0]
            x, y, w, h = cv2.boundingRect(cnt)
        else:
            laser_state = 0
        return x, y, w, h, laser_state

    def lasermain(self):
        outf = open('output2.csv', 'w')
        with picamera.PiCamera() as camera:
            # camera.resolution = (320, 240)
            camera.resolution = (640, 320)
            camera.framerate = 24
            camera.start_recording('timed.h264')
            stream = io.BytesIO()
            framecount = 0
            laserobject = laser.Laser()
            while True:
                framecount += 1
                camera.capture(stream, format="jpeg", use_video_port=True)
                frame = np.fromstring(stream.getvalue(), dtype=np.uint8)
                stream.seek(0)
                self.frame = cv2.imdecode(frame, 1)
                cv2.imshow("images", self.frame)
                cv2.waitKey(1000/24)
                starttime = time.time()
                x, y, w, h, laserstate = self.laserposition()
                print "xs", x, y, w, h, laserstate
                outf.write("x" + str(x) + "y" + str(y) + "w" + str(w) + "h" + str(h) + "laserstate" + str(laserstate) + "\n")
                laserobject.add(x, y, w, h, laserstate)
                if self.previoustate != laserstate:
                    self.previoustate = laserstate
                    if laserobject.transition % TRANSITIONS == 0:
                        laserobject.transitionscount += 1
                        self.actionx, self.actiony = laserobject.actioncoordinate()
                        clickornot = laserobject.boundaryevaluate()
                        if clickornot:
                            print "within----right or left click"
                            print "transitions counter", laserobject.transitionscount
                            #if drag is active, even if laserobject is seen as within the boundary, it will be ignored
                            if laserobject.transitionscount <= 3 and not self.dragging:
                                self.leftclick = True
                                print "left click set"
                            if laserobject.transitionscount > 3 and not self.dragging:
                                self.rightclick = True
                                self.leftclick = False
                                print "right click set"
                            laserobject.clear()
                        #possible drag
                        else:
                            print "outside----dragging"
                            print "transitions counter", laserobject.transitionscount
                            if laserobject.transitionscount > 3:
                                self.dragging = True
                                self.rightclick = False
                                self.leftclick = False
                                print "dragging from:", self.actionx, self.actiony
                            laserobject.clear()
                if x != 0:
                    try:
                        currentarea = w*h
                        if currentarea < 40:
                            outf.write("currentarea" + str(currentarea) + "\n")
                            laser.Laser.area.append(currentarea)
                            diff = laserobject.difference(laser.Laser.area)
                            outf.write("diff" + str(diff) + "\n")
                        if len(laser.Laser.area) > 15:
                            for i in xrange(0, 10):
                                laser.Laser.area.pop(0)

                        if currentarea <= 16:
                            print "blinked at:", self.actionx, self.actiony
                    except BaseException as error:
                        print "error", error

                # as soon as the transitions stop(continual beam arrives)--do a right or left click as per the flag
                if self.previoustate == laserstate:
                    print "continual beam arrived"
                    if self.leftclick:
                        print "left click at:", self.actionx, self.actiony
                        self.leftclick = False
                    if self.rightclick:
                        print "right click at:", self.actionx, self.actiony
                        self.rightclick = False
                    if self.dragging:
                        print "stop drag"
                        self.dragging = False

                    # print "simple mouse movements", x, y, w, h
                    #clear the last 7 transitions
                    laserobject.clear()
                    #clear the count of a single 7 transitions
                    laserobject.transitionscount = 0
                # endtime = time.time()
                # duration = endtime - starttime
                # print "time for algo", duration
                # outf.write("time" + str(duration) + "\n")
                # Laser.area = []
Motion().lasermain()
