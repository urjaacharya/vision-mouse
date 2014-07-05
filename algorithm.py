import cv2
from collections import Counter

###PROPOSED ARCHITECTURE_OF_LASER_MOUSE
#(within) transitionscount < 3 and continual beam after that = LEFT_CLICK
#(outside) 3 transitionscount + extra = DRAG
#(within) transitionscount > 3 and more and continual beam after that = RIGHT_CLICK


class Laser(object):
    #transition objects recorded
    x = []
    y = []
    size = []
    transition = 0
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

    def clear(self):
        # when the transition trend breaks, then clear the old transition values of x, y, size
        # and count of transitions
        Laser.x = []
        Laser.y = []
        Laser.size = []
        Laser.transition = 0

    #get the area of laser spot
    def rectarea(self):
        area = []
        for item in Laser.size:
            area.append(item[0]*item[1])
        return area

    #get difference between adjacent pixels while transitiong from on to off states
    def difference(self, params):
        return [abs(params[n] - params[n - 1]) for n in range(1, len(params))]

    #get the coordinate to start click or drag from
    def actioncoordinate(self):
        #remove the values of 0 from the lists Laser.x and Laser.y
        Laser.x = filter(lambda a: a != 0, Laser.x)
        Laser.y = filter(lambda b: b != 0, Laser.y)
        frequentx = Counter(Laser.x)
        frequentx = frequentx.most_common(1)[0][0]
        frequenty = Counter(Laser.y)
        frequenty = frequenty.most_common(1)[0][0]
        return frequentx, frequenty

    #blink within boundary is a click else drag
    def boundaryevaluate(self):
        #get difference of consecutive x and y values
        #if more near values then click else drag
        nearcount = 0 #within the NEARFACTOR limit
        farcount = 0 #outside of the NEARFACTOR limit
        localx = Laser.x
        localy = Laser.y
        xdiff = self.difference(localx)
        ydiff = self.difference(localy)
        # for x, y in zip(xdiff, ydiff):
        #     if x < NEARFACTOR and y < NEARFACTOR:
        #         nearcount += 1
        #     else:
        #         farcount += 1
        for x in xdiff:
            for y in ydiff:
                if x < NEARFACTOR and y < NEARFACTOR:
                    nearcount += 1
                    break
                else:
                    farcount += 1
                    break
        #nearcount means within boundary as per NEARFACTOR value
        if nearcount > farcount:
            return True
        else:
            return False


#ROI increment factor
NEARFACTOR = 4

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
            # CLICK/DRAG DECISION MAKING upon Transition
            if self.previoustate != laserstate:
                laserobject.add(x, y, w, h, laserstate)
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

                    else:
                        print "outside----dragging"
                        print "transitions counter", laserobject.transitionscount
                        if laserobject.transitionscount > 3:
                            self.dragging = True
                            self.rightclick = False
                            self.leftclick = False
                            print "dragging from:", self.actionx, self.actiony
                        laserobject.clear()
            #as soon as the transitions stop(continual beam arrives)--do a right or left click as per the flag
            else:
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
Motion().pccheck()