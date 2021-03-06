from Tkinter import *
import time


class SplashScreen(Frame):
    def __init__(self, master=None, width=1, height=1, useFactor=True):
        Frame.__init__(self, master)
        self.pack(side=TOP, fill=BOTH, expand=YES)

        # get screen width and height
        ws = self.master.winfo_screenwidth()
        hs = self.master.winfo_screenheight()
        w = (useFactor and ws*width) or width
        h = (useFactor and ws*height) or height
        # calculate position x, y
        x = (ws/2) - (w/2) 
        y = (hs/2) - (h/2)
        self.master.geometry('%dx%d+%d+%d' % (w, h, x, y))
        
        self.master.overrideredirect(True)
        self.lift()


def dest(root):
    print "sleeping"
    time.sleep(4)
    print "woken up"
    root.destroy()
    return

if __name__ == '__main__':
    root = Tk()
    sp = SplashScreen(root)
    sp.config(bg="#fff")
    root.after(1000, dest, root)
    root.mainloop()
