from collections import Counter

# NEARFACTOR = 3
CONTINUALBEAMTHRESH = 10

#just a Container class
class Laser(object):
    x = []
    y = []
    w = []
    h = []
    laserstate = []
    previoustate = False
    #click variables
    click = False
    dragstart = False
    decision = ''
    count = -1
    transition = 0

    def __init__(self):
        pass

    def adder(self, x, y, w, h, state):
        #appending is LAST IN operation
        self.x.append(x)
        self.y.append(y)
        self.w.append(w)
        self.h.append(h)
        self.laserstate.append(state)
        #get 15 recent samples of x and y ---> [inclusive: exclusive] slicing operation
        samplex = self.x[9:26]
        sampley = self.y[9:26]
        samplestate = self.laserstate[9:26]

        #transition block
        if self.previoustate != state:
            self.previoustate = state
            flag = self.continualbeam(samplestate, 0)
            if flag:
                self.count += 1
                if self.count == 0:
                    print "laser seen for the first time"
                    self.count = -1
            else:
                self.transition += 1
                flag1 = self.checkclick(samplex, sampley)
                # flag2 = self.checkdrag(samplex, sampley)
                if flag1:
                    print "action click"
                    self.click = True
                    if self.x[-1] == 0:
                        decision = 'c' + str(self.x[-2]) + ';' + str(self.x[-2])
                    else:
                        decision = 'c' + str(self.x[-1]) + ';' + str(self.x[-1])
                    return decision

        #continual 1 or 0's block
        else:
            self.previoustate = state
            if self.dragstart or self.click:
                flag = self.continualbeam(samplestate, 1)
                if flag:
                    self.dragstart = False
                    self.click = False
            #if laserstate is On, then only move
            if state:
                decision = 'm' + str(self.x[-1]) + str(self.y[-1])
                return decision

        self.bufferclear()

    def checkclick(self, samplex, sampley):
        if self.transition == 1:
            if abs(samplex[-1] - samplex[-2]) <= 4:
                return True
            else:
                return False

    # def checkdrag(self, samplex, sampley):

    #check for continuous 0's or 1's within the CONTINUALBEAMTHRESH
    def continualbeam(self, samplestate, factor):
        continual = 0
        for state in samplestate:
            if state == factor:
                continual += 1
                if continual >= CONTINUALBEAMTHRESH:
                    self.transition = 0
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

    def clear(self):
        self.x = []
        self.y = []
        self.w = []
        self.h = []
        self.laserstate = []

    # def difference(self, params):
    #     return [abs(params[n] - params[n - 1]) for n in range(1, len(params))]
    #
    # def actioncoordinate(self):
    #     Laser.x = filter(lambda a: a != 0, Laser.x)
    #     Laser.y = filter(lambda b: b != 0, Laser.y)
    #     frequentx = Counter(Laser.x)
    #     frequentx = frequentx.most_common(1)[0][0]
    #     frequenty = Counter(Laser.y)
    #     frequenty = frequenty.most_common(1)[0][0]
    #     return frequentx, frequenty
    #
    # def boundaryevaluate(self):
    #     nearcount = 0
    #     farcount = 0
    #     localx = Laser.x
    #     localy = Laser.y
    #     xdiff = self.difference(localx)
    #     ydiff = self.difference(localy)
    #     for x, y in zip(xdiff, ydiff):
    #         if x < NEARFACTOR and y < NEARFACTOR:
    #             nearcount += 1
    #         else:
    #             farcount += 1
    #     if nearcount > farcount:
    #         return True
    #     else:
    #         return False