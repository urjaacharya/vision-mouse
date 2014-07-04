import cv2
from collections import Counter

###ARCHITECTURE_OF_LASER_MOUSE
#(within) 3 transitionscount = RIGHT_CLICK
#(outside) 3 transitionscount + extra = DRAG
#(within) transitionscount < 3 = LEFT_CLICK


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
        Laser.x.append(x)
        Laser.y.append(y)
        Laser.size.append((w, h))
        #transition = counter of on/off laser objects
        Laser.laserstate.append(state)
        if Laser.transition > 7:
            Laser.transitionscount += 1
            print "transitionscount", Laser.transitionscount

    def clear(self):
        # when the transition trend breaks, then clear the old transition values of x, y, size
        # and count of transitions
        Laser.transition = 0
        Laser.x = []
        Laser.y = []
        Laser.size = []

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

        #remove the values of 0 from the lists Laser.x and Laser.y
        Laser.x = filter(lambda a: a != 0, Laser.x)
        Laser.y = filter(lambda b: b != 0, Laser.y)

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
        xdiff = self.difference(localx)
        ydiff = self.difference(localy)

        for x, y in zip(xdiff, ydiff):
            if x < ROIFACTOR and y < ROIFACTOR:
                nearcount += 1
            else:
                farcount += 1

        #nearcount means within boundary as per ROIFACTOR value
        if nearcount > farcount:
            return True
        else:
            return False


#ROI increment factor
ROIFACTOR = 2

#decision making value for click or drag, in a click atleast 7on/off states are visible
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
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 1, cv2.CV_AA)
            cv2.imshow("images", frame)
            cv2.waitKey(42)
        else:
            laser_state = 0
        return x, y, w, h, laser_state

    # algorithm check on computer
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
                # print "transition", laserobject.transition, laserobject.x, laserobject.y
                if laserobject.transition % TRANSITIONS == 0: #and not self.buttonpress and not self.dragging:
                    # print "on/off:", laserobject.transition
                    clickornot = laserobject.boundaryevaluate()
                    if clickornot:
                        self.actionx, self.actiony = laserobject.actioncoordinate()
                        print "action-x:", self.actionx, "action-y:", self.actiony
                        if laserobject.transitionscount <= 3:
                            self.leftclick = True
                            print "left click set"
                        elif laserobject.transitionscount > 3:
                            self.rightclick = True
                            self.leftclick = False
                            print "right click set"
                        laserobject.clear()

                    else:
                        if laserobject.transitionscount > 3 and not self.dragging:
                            self.dragging = True

                        if self.dragging:
                            print "dragging from:", self.actionx, self.actiony
                        laserobject.clear()

            else:
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
                laserobject.clear()
                laserobject.transitionscount = 0
Motion().pccheck()