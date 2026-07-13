from gpiozero import MotionSensor   #Allows for high-level interface for PIR sensors
from signal import pause            #Import pause() so the program runs indefinitely

#Create a MotionSensor Object connected to GPIO17
#Corresponds to Physical Pin 11 on the Raspberry Pi
pir = MotionSensor(17)

#Startup Messages
print("Motion sensor initialized")
print("Waiting for motion...")

#Print to terminal when motion is and is no longer detected
pir.when_motion = lambda: print("MOTION DETECTED")  #Run this code when motion
pir.when_no_motion = lambda: print("Motion ended")

#Keep program running and listening for sensor events.
pause()