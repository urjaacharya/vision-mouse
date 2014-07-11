from collections import Counter

NEARFACTOR = 3


#just a Container class
class Laser(object):
    x = []
    y = []
    w = []
    h = []
    laserstate = []
    transition = 0
    previoustate = False

    def __init__(self):
        pass

    def adder(self, x, y, w, h, state):
        Laser.x.append(x)
        Laser.y.append(y)
        Laser.w.append(w)
        Laser.h.append(h)
        Laser.laserstate.append(state)
        if state != Laser.previoustate:
            self.transition += 1
        else:
            self.transition = 0
        Laser.previoustate = state

    def clear(self):
        Laser.x = []
        Laser.y = []
        Laser.size = []
        Laser.transition = 0

    def difference(self, params):
        return [abs(params[n] - params[n - 1]) for n in range(1, len(params))]

    def actioncoordinate(self):
        Laser.x = filter(lambda a: a != 0, Laser.x)
        Laser.y = filter(lambda b: b != 0, Laser.y)
        frequentx = Counter(Laser.x)
        frequentx = frequentx.most_common(1)[0][0]
        frequenty = Counter(Laser.y)
        frequenty = frequenty.most_common(1)[0][0]
        return frequentx, frequenty

    def boundaryevaluate(self):
        nearcount = 0
        farcount = 0
        localx = Laser.x
        localy = Laser.y
        xdiff = self.difference(localx)
        ydiff = self.difference(localy)
        for x, y in zip(xdiff, ydiff):
            if x < NEARFACTOR and y < NEARFACTOR:
                nearcount += 1
            else:
                farcount += 1
        if nearcount > farcount:
            return True
        else:
            return False