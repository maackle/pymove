import sys
import os
import time
import psmove
import copy
import math
from util import *

class ConnectionType:
    BLUETOOTH = psmove.Conn_Bluetooth
    USB = psmove.Conn_USB
    UNKNOWN = psmove.Conn_Unknown
    name = {BLUETOOTH:"Bluetooth", USB:"USB", UNKNOWN:"Unknown"}

class Button:
    L2 = psmove.Btn_L2
    R2 = psmove.Btn_R2
    L1 = psmove.Btn_L1
    R1 = psmove.Btn_R1
    TRIANGLE = psmove.Btn_TRIANGLE
    CIRCLE = psmove.Btn_CIRCLE
    CROSS = psmove.Btn_CROSS
    SQUARE = psmove.Btn_SQUARE
    SELECT = psmove.Btn_SELECT
    L3 = psmove.Btn_L3
    R3 = psmove.Btn_R3
    START = psmove.Btn_START
    UP = psmove.Btn_UP
    RIGHT = psmove.Btn_RIGHT
    DOWN = psmove.Btn_DOWN
    LEFT = psmove.Btn_LEFT
    PS = psmove.Btn_PS
    MOVE = psmove.Btn_MOVE
    T = psmove.Btn_T
    All = (L2, R2, L1, R1, TRIANGLE, CIRCLE, CROSS, SQUARE, SELECT, L3, R3, START, UP, RIGHT, DOWN, LEFT, PS, MOVE, T)

class Battery:
    MIN = psmove.Batt_MIN
    MAX = psmove.Batt_MAX
    CHARGING = psmove.Batt_CHARGING

class Event:
    NADA = 0
    JERK = 1
    Total = 2

class MoveController(psmove.PSMove):
    total = 0
    def __init__(self, id = 0):
        super(MoveController,self).__init__(id)
        self.id = id
        self.clock = 0
        self.buttons = 0
        self.prevButtons = 0
        self.buttonTime = {}
        self.eventTime = [None]*Event.Total
        for b in Button.All:
            self.buttonTime[b] = None
        for i in range(Event.Total):
            self.eventTime[i] = None

        # jerking!
        self.memAccel = Mem(5, vec(0,0,0))
        self.memJerk = Mem(5, vec(0,0,0))
        self.jerkDelay = 0.25 # seconds
        self.jerkThresh = 0.5
        self.jerkThreshRatio = 0.5
        self.jerkPeak = 0
        self.jerkOK = False

        # calibration
        self.deadzone = 0.0
        self.dzLow = vec()
        self.dzHigh = vec()
        self.isCalibrating = False
        self.calibrationSteps = 0
        MoveController.total += 1

    def color(self, *o):
        if len(o)==1:
            col = o[0]
            if(type(col) is Colori):
                self.set_leds(col.tup())
            elif(type(col) is Colorf):
                self.set_leds(col.toByte().tup())
            elif(len(o[0])==3):
                self.set_leds(*o[0])
        elif len(o)==3:
            self.set_leds(int(o[0]), int(o[1]), int(o[2]))
    @property
    def rawAccel(self):
        return vec(self.ax, self.ay, self.az)
    @property
    def accel(self):
        return self.rawAccel / 4000.0
    @property
    def jerk(self):
        return self.memAccel.now - self.memAccel.prev
    @property
    def gyro(self):
        return vec(self.gx, self.gy, self.gz)
    @property
    def magnet(self):
        return vec(self.mx, self.my, self.mz)
    @property
    def connection(self):
        return ConnectionType.name[psmove.psmove_connection_type(self)]
    def buttonDown(self, b):
        return self.buttons & b
    def buttonPressed(self, b):
        return (self.buttons & b) and not (self.prevButtons & b)
    def buttonReleased(self, b):
        return not (self.buttons & b) and (self.prevButtons & b)
    def buttonDuration(self, b):
        if(self.buttonTime[b] == None): 
            return float("inf")
        else: 
            d = (now() - self.buttonTime[b])
            return d.seconds + d.microseconds/1000000.0
    def eventDuration(self, b):
        if(self.eventTime[b] == None): 
            return float("inf")
        else: 
            d = (now() - self.eventTime[b])
            return d.seconds + d.microseconds/1000000.0
    
    def input(self):
        raise Exception("must implement in subclass")
    def output(self):
        raise Exception("must implement in subclass")

    def checkJerk(self, thresh):
        def doJerk():
            self.onJerk()
            self.eventTime[Event.JERK] = now()
            self.jerkOK = False

        prev = self.memJerk.prev.length
        current = self.memJerk.now.length
        diff = self.jerk.length
        if(current > thresh): 
            pass
        if self.jerkOK and prev > current and prev > thresh and self.eventDuration(Event.JERK) > self.jerkDelay:
            doJerk()
        if current < thresh * self.jerkThreshRatio:
            self.jerkOK = True

    def tick(self):
        if self.poll():
            self.buttons = self.get_buttons()
            if(self.buttons != self.prevButtons):
                for b in Button.All:
                    if(self.buttonDown(b)):
                        self.buttonTime[b] = now()
            self.memAccel << self.accel
            self.memJerk << self.jerk
            self.checkJerk(self.jerkThresh)

            ############
            self.input()
            ############

            # always last
            self.prevButtons = self.buttons
        
        #############
        self.output()
        #############

        self.update_leds()
        self.clock += 1

class Framework:

    def __init__(self, klass):
        self.controllers = []

    ###TODO: assert klass isInstanceOf MoveController
    def addAll(self, klass):
        assert(type(klass) is type)
        count = psmove.count_connected()
        if(count == 0):
            print "No Move controllers found..."
            sys.exit()
        else:
            print "Connecting %i controller(s):\n"%count
            for i in range(count):
                move = klass(i)
                print i, ": ", move.connection
                self.controllers.append(move)
            print "Success"

    def run(self):

        while True:
            for move in self.controllers:
                move.tick()

            time.sleep(.01)













