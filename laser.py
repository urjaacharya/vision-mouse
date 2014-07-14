import socket
from collections import Counter

THRESHHOLD = 4


class Laser(object):
    x = []
    y = []
    w = []
    h = []
    laserstate = []
    previoustate = False
    client = None

    def __init__(self, clientsocket):
        self.client = clientsocket

        #states
        self.continualzero = None
        self.continualone = None
        self.toggleto0 = None
        self.toggleto1 = None
        self.one = 0
        self.zero = 0

    def container(self, x, y, w, h, state):
        self.x.append(x)
        self.y.append(y)
        self.w.append(w)
        self.h.append(h)
        self.laserstate.append(state)

        #first we clear the buffer to size 10 before making any analysis
        self.bufferclear()

        #no states have been initialized to
        if self.continualzero is None and self.continualone is None and self.toggleto0 is None and self.toggleto1 is None:
            continualzero = self.continualbeam(self.laserstate, 0)
            if not continualzero:
                self.continualzero = False
                continualone = self.continualbeam(self.laserstate, 1)
                if not continualone:
                    self.continualone = False
                    toggleto0 = self.toggle(state)
                    if toggleto0:
                        self.toggleto0 = toggleto0
                        self.zero += 1
                    else:
                        self.toggleto1 = True
                        self.one += 1
                else:
                    self.continualone = True
            else:
                self.continualzero = True

        if self.continualzero:
            if state == 1:
                self.toggleto1 = True
                self.continualzero = False
                self.continualone = False
                self.toggleto0 = False
            else:
                print "we send nothing"

        if self.continualone:
            if state == 0:
                self.toggleto0 = True
                self.continualone = False
                self.continualzero = False
                self.toggleto1 = False
                self.client.send('md' + str(self.x[-2]) + ';' + str(self.y[-2]) + '\0')
            else:
                self.client.send('m' + str(self.x[-1]) + ';' + str(self.y[-1]) + '\0')

        if self.toggleto0:
            if state == 1:
                self.toggleto1 = True
                self.toggleto0 = False
                self.continualzero = False
                self.continualone = False
                self.client.send('md' + str(self.x[-1]) + ';' + str(self.y[-1]) + '\0')
            else:
                self.zero += 1
                if self.zero > THRESHHOLD:
                    self.toggleto0 = False
                    self.continualzero = True
                    print "went outside"

        if self.toggleto1:
            if state == 0:
                self.toggleto0 = True
                self.toggleto1 = False
                self.continualone = False
                self.continualzero = False
                self.client.send('md' + str(self.x[-2]) + ';' + str(self.y[-2]) + '\0')
            else:
                self.one += 1
                if self.one > THRESHHOLD:
                    self.toggleto1 = False
                    self.continualone = True
                self.client.send('m' + str(self.x[-1]) + ';' + str(self.y[-1]) + '\0')

    def toggle(self, state):
        if self.previoustate != state and state == 0:
            print "1 to 0"
            return True
        elif self.previoustate != state and state == 1:
            print "0 to 1"
            return False

    # check for continuous 0's or 1's within the CONTINUALBEAMTHRESH
    def continualbeam(self, samplestate, factor):
        continual = 0
        for state in samplestate:
            if state == factor:
                continual += 1
                if continual >= CONTINUALBEAMTHRESH:
                    return True
            else:
                return False

    def bufferclear(self):
        # buffer clear if length of buffer equal 25
        if len(self.x) == 25:
            for i in range(0, 10):
                self.x.pop(0)
                self.y.pop(0)
                self.w.pop(0)
                self.h.pop(0)
                self.laserstate.pop(0)
