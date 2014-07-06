from collections import Counter

class Laser(object):
    #transition objects recorded
    x = []
    y = []
    w = []
    h = []
    # size = []
    area = []
    transition = 0
    laserstate = []
    transitionscount = 0

    def __init__(self):
        pass

    def add(self, x, y, w, h, state):
        Laser.transition += 1
        Laser.x.append(x)
        Laser.y.append(y)
        Laser.w.append(w)
        Laser.h.append(h)
        # Laser.size.append((w, h))
        #transition = counter of on/off laser objects
        Laser.laserstate.append(state)

    def clear(self):
        # when the transition trend breaks, then clear the old transition values of x, y, size
        # and count of transitions
        Laser.x = []
        Laser.y = []
        Laser.size = []
        Laser.transition = 0

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
        for x, y in zip(xdiff, ydiff):
            if x < NEARFACTOR and y < NEARFACTOR:
                nearcount += 1
            else:
                farcount += 1
        #nearcount means within boundary as per NEARFACTOR value
        if nearcount > farcount:
            return True
        else:
            return False