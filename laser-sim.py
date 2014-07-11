from Tkinter import *
import time

class MouseLocation( Frame ):
   recording = False
   mouseDown = False
   laserOn = False
   fil = open("sim.dat", "w")
   toWrite = 0
   lastWriten = 0
   def __init__( self ):
      Frame.__init__( self )
      self.pack( expand = YES, fill = BOTH )
      self.master.title( "Demonstrating Mouse Events" )
      self.master.geometry(  "275x275" )
      
      self.mousePosition = StringVar() # displays mouse position
      self.mousePosition.set( "Mouse outside window" )
      self.positionLabel = Label( self,textvariable = self.mousePosition )
      self.positionLabel.pack( side = BOTTOM )

      self.bind( "<Button-1>", self.buttonPressed )
      self.bind( "<ButtonRelease-1>", self.buttonReleased )   
      self.bind( "<Enter>", self.enteredWindow )
      self.bind( "<Leave>", self.exitedWindow )
      self.bind( "<B1-Motion>", self.mouseDragged )
      self.bind( "<Motion>", self.mouseMoved )
      
      self.master.bind( "<KeyPress-Shift_L>", self.shiftPressed )
      self.master.bind( "<KeyRelease-Shift_L>", self.shiftReleased )

   def shiftPressed( self, event ):
      self.mousePosition.set( "Recording" )
      self.recording = True

   def shiftReleased( self, event ):
      self.mousePosition.set( "Stopped recording" )
      self.recording = False

   def buttonPressed( self, event ):
      self.mousePosition.set( "Pressed at [ " + str( event.x ) + ", " + str( event.y ) + " ]" )
      self.mouseDown = True

   def buttonReleased( self, event ):
      self.mousePosition.set( "Released at [ " + str( event.x ) + ", " + str( event.y ) + " ]" )
      self.mouseDown = False

   def enteredWindow( self, event ):
      self.mousePosition.set( "Mouse in window" )
      self.laserOn = True

   def exitedWindow( self, event ):
      self.mousePosition.set( "Mouse outside window" )
      self.laserOn = False

   def mouseDragged( self, event ):
      self.mousePosition.set( "Dragged at [ " + str( event.x ) + ", " + str( event.y ) + " ]" )
      self.toWrite = (self.toWrite + 1)%2
      if self.recording == True:
         self.writeFile(str(self.toWrite)+","+str(event.x)+","+str(event.y) +"\r\n")

   def mouseMoved( self, event ):
      self.mousePosition.set( "Moved to [ " + str( event.x ) + ", " + str( event.y ) + " ]" )
      self.toWrite = 1
      if self.recording == True:
         self.writeFile(str(self.toWrite)+","+str(event.x)+","+str(event.y) +"\r\n")
      
   def writeFile( self, string ):
      now = time.time()
      if now - self.lastWriten > .042:
        self.fil.write( string )
        self.lastWriten = now
MouseLocation().mainloop()
