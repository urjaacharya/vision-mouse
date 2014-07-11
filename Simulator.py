
class Simulator(object):

    fil = open("sim.dat", "r")
    
    def __init__(self):        
        pass
        
    def getNext( self ):
        line = self.fil.readline()
        if len(line) == 0:
            return -1, -1, -1
        parts = line.split(",")
        return int(parts[0]), int(parts[1]), int(parts[2])
