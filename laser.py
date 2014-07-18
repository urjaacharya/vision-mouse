import socket

#number of ones or zeros to be considered continual
THRESHHOLD = 6
CLICK = 3


class Laser(object):
    #coordinates x, y of laser
    x = []
    y = []
    #approx width and height of laser
    w = []
    h = []
    laserstate = []
    previoustate = False#previous state of laser initialized to False(no laser seen)
    client = None#client is None at first

    def __init__(self, clientsocket):
        self.client = clientsocket

        #states
        self.continualzero = False#continual zeros
        self.continualone = False#continual ones
        self.toggle1to0 = False#one to zero
        self.toggle0to1 = False#zero to one
        self.one = 0#number of ones in toggle0to1 state before reaching threshold for continualone
        self.zero = 0#number of zeros in toggle1to0 state before reaching threshold for continualzero

        self.transition1 = 0
        self.mousedown = False
        self.dragstart = False

    def container(self, x, y, w, h, state):
        self.x.append(x)
        self.y.append(y)
        self.w.append(w)
        self.h.append(h)
        self.laserstate.append(state)

        #first we clear the buffer to size 10 before making any analysis
        self.bufferclear()

        #to initialize to a state, after a reset or when starting for first time
        if self.continualzero is False and self.continualone is False and self.toggle1to0 is False and self.toggle0to1 \
                is False:
            #continuity is checked from last of the list
            continualzero = self.continualbeam(self.laserstate[:: -1], 0)
            if not continualzero:
                self.continualzero = False
                continualone = self.continualbeam(self.laserstate[:: -1], 1)
                if not continualone:
                    self.continualone = False
                    toggle1to0 = self.toggle(state)
                    if toggle1to0:
                        self.toggle1to0 = True
                        self.zero += 1
                    else:
                        self.toggle0to1 = True
                        self.one += 1
                else:
                    self.continualone = True
            else:
                self.continualzero = True

            return

        # send "m" for move("m")
        # send "md" for mouse down("md")
        # send "mr" for mouse release("mr")
        #TODO boundary check has not been implemented
        if self.continualzero:
            if state == 1:
                self.toggle0to1 = True
                self.continualzero = False
                self.client.send('m' + ';' + str(self.x[-1]) + ';' + str(self.y[-1]) + '\0')
            else:
                print "still zero"
            return

        if self.continualone:
            if state == 0:
                self.toggle1to0 = True
                self.continualone = False
            else:
                self.client.send('m' + ';' + str(self.x[-1]) + ';' + str(self.y[-1]) + '\0')
                print "still one"
            return

        if self.toggle1to0:
            if state == 1:
                self.toggle0to1 = True
                self.toggle1to0 = False
                self.client.send('m' + ';' + str(self.x[-1]) + ';' + str(self.y[-1]) + '\0')
                self.transition1 += 1
                if self.transition1 == CLICK:
                    self.mousedown = True
                elif self.transition1 > CLICK:
                    self.dragstart = True
                if self.dragstart:
                    self.client.send('md' + ';' + str(self.x[-1]) + ';' + str(self.y[-1]) + '\0')
            else:
                self.zero += 1
                if self.zero == THRESHHOLD:
                    ind = self.indexes(self.laserstate)
                    self.continualzero = True
                    self.toggle1to0 = False
                    if self.dragstart:
                        self.client.send('mr' + ';' + str(self.x[ind]) + ';' + str(self.y[ind]) + '\0')
                    if self.mousedown:
                        self.client.send('mr' + ';' + str(self.x[ind]) + ';' + str(self.y[ind]) + '\0')
                    self.mousedown = False
                    self.dragstart = False
                    self.transition1 = 0
            return

        if self.toggle0to1:
            if state == 0:
                self.toggle1to0 = True
                self.toggle0to1 = False
                self.transition1 += 1
                if self.transition1 == CLICK:
                    self.mousedown = True
                if self.transition1 > CLICK:
                    self.dragstart = True
                if self.dragstart:
                    self.client.send('md' + ';' + str(self.x[-2]) + ';' + str(self.y[-2]) + '\0')
            else:
                self.one += 1
                ind = self.indexes(self.laserstate)
                self.client.send('m' + ';' + str(self.x[ind]) + ';' + str(self.y[ind]) + '\0')
                if self.one == THRESHHOLD:
                    self.toggle0to1 = False
                    self.continualone = True
                    if self.mousedown:
                        self.client.send('md' + ';' + str(self.x[ind]) + ';' + str(self.y[ind]) + '\0')
                        self.client.send('mr' + ';' + str(self.x[ind]) + ';' + str(self.y[ind]) + '\0')
                    if self.dragstart:
                        self.client.send('mr' + ';' + str(self.x[ind]) + ';' + str(self.y[ind]) + '\0')
                    self.mousedown = False
                    self.dragstart = False
                    self.transition1 = 0
            return

    #checks the toggle of states, and returns True if toggle is from 1to0 and False if toggle is from 0to1
    def toggle(self, state):
        if self.previoustate != state and state == 0:
            print "1 to 0"
            return True
        elif self.previoustate != state and state == 1:
            print "0 to 1"
            return False

    # factor can be 0 or 1, this function will check for continuous 1 or 0 within threshold and return True
    def continualbeam(self, samplestate, factor):
        continual = 0
        for state in samplestate:
            if state == factor:
                continual += 1
                if continual >= THRESHHOLD:
                    return True
            else:
                return False

    # buffer clear if length of buffer equal 20--->pop 10 of them, First In First Out(FIFO)
    def bufferclear(self):
        if len(self.x) == 20:
            for i in range(0, 10):
                self.x.pop(0)
                self.y.pop(0)
                self.w.pop(0)
                self.h.pop(0)
                self.laserstate.pop(0)

    #get index of laser state one from last
    def indexes(self, states):
        ind = 0
        for i, data in enumerate(states):
            if data == 1:
                ind = i
        return ind