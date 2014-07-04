import cv2
# import time
# import picamera
import numpy as np
# from math import fabs, sqrt
from collections import Counter


class Laser(object):
    #transition objects recorded
    transition = 0
    x = []
    y = []
    size = []
    laserstate = []
    transitionscount = 0

    def __init__(self):
        pass

    def add(self, x, y, w, h, state):
        Laser.transition += 1
        #x, y's value is zero = OFF value = ON
        # if x != 0 and y != 0:
        #     Laser.laserstate.append(True)
        # else:
        #     Laser.laserstate.append(False)
        Laser.x.append(x)
        Laser.y.append(y)
        Laser.size.append((w, h))
        #transition = counter of on/off laser objects
        Laser.laserstate.append(state)
        if Laser.transition > 7:
            Laser.transitionscount += 1

    def clear(self):
        # when the transition trend breaks, then clear the old transition values of x, y, size
        # and count of transitions
        Laser.transition = 0
        Laser.x = []
        Laser.y = []
        Laser.size = []
        Laser.transitionscount = 0

    #get the area of laser spot
    def rectarea(self):
        area = []
        for item in Laser.size:
            area.append(item[0]*item[1])
        return area

    #get difference between adjacent pixels while transiting from on to off states
    def difference(self, params):
        return [abs(params[n] - params[n - 1]) for n in range(1, len(params))]

    #get the coordinate to start click or drag from
    def actioncoordinate(self):

    #remove the values of 0 from the Laser.x and Laser.y lists
        Laser.x = filter(lambda a: a != 0, Laser.x)
        Laser.y = filter(lambda b: b != 0, Laser.y)
        # for x in Laser.x:
        #     if x == 0:
        #         i = Laser.x.index(x)
        #         Laser.x.pop(i)
        # for y in Laser.y:
        #     if y == 0:
        #         j = Laser.y.index(y)
        #         Laser.y.pop(j)

        commonx = Counter(Laser.x)
        commonx = commonx.most_common(1)[0][0]
        commony = Counter(Laser.y)
        commony = commony.most_common(1)[0][0]

        return commonx, commony

    #blink within boundary is a click else drag
    def boundaryevaluate(self):
        #get difference of consecutive x and y values
        #if more near values then click else drag
        nearcount = 0 #within the ROIFACTOR limit
        farcount = 0 #outside of the ROIFACTOR limit
        localx = Laser.x
        localy = Laser.y
        #size variations for click
        # areas = self.rectarea()
        xdiff = self.difference(localx)
        ydiff = self.difference(localy)

        for x in xdiff:
            for y in ydiff:
                #size variations for click
                # for area in areas:
                #     if area < 200:
                if x < ROIFACTOR and y < ROIFACTOR:
                    nearcount += 1
                    break
                else:
                    farcount += 1
                    break

        if nearcount > farcount:
            return True
        else:
            return False


#ROI increment factor
ROIFACTOR = 4

#decision making value for click or drag, in a click atleast 7on/off states are visible
TRANSITIONS = 7

#remove small pixel motions
JERKS = 2


class Motion(object):
    def __init__(self):

        self.frame = None
        #boundary
        self.boundx = 0
        self.boundy = 0
        self.boundw = 640
        self.boundh = 480
        #states
        self.previoustate = 0
        self.objects = []
        self.sequence = 0
        #old x, y, w, h
        self.x = 0
        self.y = 0
        self.w = 0
        self.h = 0

    def gettransformedboundingrect(self, x, y, w, h):
        w *= ROIFACTOR
        h *= ROIFACTOR
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
        #else send the old value which is self
        return self.x, self.y, self.w, self.h

    def laserposition(self):
        frame = self.frame
        x = y = w = h = 0
        #for roi
        # img = img[y1:y2, x1:x2]
        # frame = frame[self.boundy: self.boundy + self.boundh, self.boundx: self.boundx + self.boundw]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        ret, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) > 0:
            laser_state = 1
            cnt = contours[0]
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 1, cv2.CV_AA)
            cv2.imshow("images", frame)
            cv2.waitKey(42)
            #for roi
            # x += self.boundx
            # y += self.boundy
            # self.boundx, self.boundy, self.boundw, self.boundh = self.gettransformedboundingrect(x, y, w, h)
        else:
            laser_state = 0
            #for roi
            # self.boundx = 0
            # self.boundy = 0
            # self.boundw = 640
            # self.boundh = 480
        return x, y, w, h, laser_state

    # computer
    def pccheck(self):
        capture = cv2.VideoCapture("blinkie.h264")
        laserobject = Laser()
        while capture.isOpened():
            ret, frame = capture.read()
            self.frame = frame
            if frame is None:
                break
            x, y, w, h, laserstate = self.laserposition()
            # print "x:", x, "y:", y, "w:", w, "h:", h, "state:", laserstate
            # CLICK/DRAG DECISION MAKING upon Transition
            if self.previoustate != laserstate:
                # print "pre:", self.previoustate, "post:", laserstate
                laserobject.add(x, y, w, h, laserstate)
                self.previoustate = laserstate
                print "transition", laserobject.transition, laserobject.x, laserobject.y
                if laserobject.transition % TRANSITIONS == 0: #and not self.buttonpress and not self.dragging:
                    print "on/off:", laserobject.transition
                    actionx, actiony = laserobject.actioncoordinate()
                    print "actionx:", actionx, "actiony:", actiony
                    clickornot = laserobject.boundaryevaluate()
                    if clickornot:
                        print "click at:", actionx, actiony
                        self.buttonpress = True
                        laserobject.clear()
                        # break
                    else:
                        print "drag start at:", actionx, actiony
                        self.dragging = True
                        laserobject.clear()
                        # break

                # else:
                #     if laserobject.transition % 2 == 0:
                #         if self.buttonpress:
                #             print "click by mouse"
                #         elif self.dragging:
                #             print "dragging the mouse"

            else:
                self.buttonpress = False
                self.dragging = False
                # laserobject.transition = 0
                # x, y, w, h = self.removejerks(x, y, w, h)
                print "simple mouse movements", x, y, w, h
                laserobject.clear()
#pc
Motion().pccheck()