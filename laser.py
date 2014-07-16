import socket

#number of ones or zeros to be considered continual
THRESHHOLD = 4
#number of transitions to begin Drag
TRANS = 2


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
        self.continualzero = None#continual zeros
        self.continualone = None#continual ones
        self.toggle1to0 = None#one to zero
        self.toggle0to1 = None#zero to one
        self.one = 0#number of ones in toggle0to1 state before reaching threshold for continualone
        self.zero = 0#number of zeros in toggle1to0 state before reaching threshold for continualzero

        self.transition1 = 0
        self.transition2 = 0

    def container(self, x, y, w, h, state):
        self.x.append(x)
        self.y.append(y)
        self.w.append(w)
        self.h.append(h)
        self.laserstate.append(state)

        #first we clear the buffer to size 10 before making any analysis
        self.bufferclear()

        #to initialize to a state, after a reset or when starting for first time
        if self.continualzero is None and self.continualone is None and self.toggle1to0 is None and self.toggle0to1 is None:
            continualzero = self.continualbeam(self.laserstate, 0)
            if not continualzero:
                self.continualzero = False
                continualone = self.continualbeam(self.laserstate, 1)
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
            self.transition1 = 0
            self.transition2 = 0
            if state == 1:
                #continual zero to state 1 means laser is in camera view now
                self.toggle0to1 = True
                #MOVE
                self.client.send('m' + ';' + str(self.x[-1]) + ';' + str(self.y[-1]) + '\0')
                #make all else False
                self.toggle1to0 = False
                self.continualone = False
                self.continualzero = False
            else:
                print "no laser seen-->do nothing"
            return

        if self.continualone:
            self.transition1 = 0
            self.transition2 = 0
            if state == 0:
                self.toggle1to0 = True
                #x[-2] is sent because current state has x value=0, so we mouse down at previous x's value which
                # is surely one since we toggled from 1 to 0
                # toggle occurred from 1 to 0
                #MOUSE DOWN
                self.client.send('md' + ';' + str(self.x[-2]) + ';' + str(self.y[-2]) + '\0')
                #make all else False
                self.continualone = False
                self.continualzero = False
                self.toggle0to1 = False
            else:
                #when laser is still on, send move command
                #MOVE
                self.client.send('m' + ';' + str(self.x[-1]) + ';' + str(self.y[-1]) + '\0')
            return

        if self.toggle1to0:
            if state == 1:
                #toggled to 1 from 0 again--->still send a mouse down
                self.toggle0to1 = True
                self.transition1 += 1
                if self.transition1 <= TRANS and self.transition2 <= TRANS:
                    #MOVE
                    self.client.send('m' + ';' + str(self.x[-1]) + ';' + str(self.y[-1]) + '\0')
                #MOUSE DOWN
                self.client.send('md' + ';' + str(self.x[-1]) + ';' + str(self.y[-1]) + '\0')
                #make all else False
                self.toggle1to0 = False
                self.continualzero = False
                self.continualone = False
            else:
                #zero came in sequence
                self.zero += 1
                if self.zero == THRESHHOLD:
                    self.toggle1to0 = False
                    self.continualzero = True
                    #MOUSE RELEASE
                    self.client.send('mr' + ';' + str(self.x[-3]) + ';' + str(self.y[-3]) + '\0')
                    print "went outside of screen"
            return

        if self.toggle0to1:
            if state == 0:
                self.toggle1to0 = True
                self.transition2 += 1
                if self.transition1 <= TRANS and self.transition2 <= TRANS:
                    #MOUSE DOWN AND MOVE
                    self.client.send('md' + ';' + str(self.x[-2]) + ';' + str(self.y[-2]) + '\0')
                    self.client.send('m' + ';' + str(self.x[-2]) + ';' + str(self.y[-2]) + '\0')
                else:
                    #MOUSE DOWN
                    self.client.send('md' + ';' + str(self.x[-2]) + ';' + str(self.y[-2]) + '\0')
                # make all else False
                self.toggle0to1 = False
                self.continualone = False
                self.continualzero = False

            else:
                self.one += 1
                if self.one == THRESHHOLD:
                    self.toggle0to1 = False
                    self.continualone = True
                    #MOUSE RELEASE
                    self.client.send('mr' + ';' + str(self.x[-1]) + ';' + str(self.y[-1]) + '\0')
                #MOVE
                self.client.send('m' + ';' + str(self.x[-1]) + ';' + str(self.y[-1]) + '\0')
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
