#new module for MAVproxy
'''
    autoland - displays autolanding HUD
'''

import math, numpy as np, sys, pygame

mpstate = None

class module_state(object):
    #stores the state of this module - values that the main process needs?
    def __init__(self):
        self.gps = [0,0]#lat, long
        self.ahrs = [0,0,0]#roll,pitch,yaw
        self.aspeed = 0
        self.alt = 0#altitude (m)
        self.lam = 0#localizer angle
        self.gam = 0#glideslope angle
        self.loc = [0,0,0]#postion vector in runway-centric coords
        self.RE = 6378100.0#earth radius in metres
        #constants defining the runway LOCATION and DIRECTION
        self.cos_eta_r = -.7071
        self.sin_eta_r = .7071
        self.LOC_LONG = -964855190
        self.LOC_LAT = 306382350
    def update_gps(self,lat,lon):
        self.gps = [lat,lon]
        #local GPS coords
        lat_rel = self.gps[0]-self.LOC_LAT
        long_rel = self.gps[1] - self.LOC_LONG
        #runway centric x-y-z coords in m?
        x = 1e-7*self.RE*(math.radians(lat_rel)*self.cos_eta_r + math.radians(long_rel)*self.sin_eta_r)
        y = 1e-7*self.RE*(-math.radians(lat_rel)*self.sin_eta_r + math.radians(long_rel)*self.cos_eta_r)
        self.loc = [x,y,-self.alt]
        #update gamma, lambda
        self.gam = math.degrees( math.atan(self.alt/abs(x)) )
        self.lam = math.degrees( math.atan(-1.0*y/abs(x)) )
    def update_ahrs(self,roll,pitch,yaw):
        self.ahrs = [roll, pitch, yaw]
    def update_aspeed(self,speed):
        self.aspeed = speed
    def update_alt(self,altitude):
        self.alt = altitude
    def get_gps(self):
        return self.gps
    def get_ahrs(self):
        return self.ahrs
    def get_aspeed(self):
        return self.aspeed
    def get_alt(self):
        return self.alt

def name():
    return "autoland"

def description():
    return "Autolanding status GUI"

def init(_mpstate):
    global mpstate
    mpstate = _mpstate
    mpstate.autoland_state = module_state()#have to add this member to the mpstate class definition
    #do everything else that has to happen on startup
    #run the pygame stuff

def unload():
    pass
    #kill everything

def mavlink_packet(msg):
    #handle an incoming mavlink packet
    mtype = msg.get_type()
    
    master = mpstate.master()
    state = mpstate.autoland_state
    if mtype == 'GLOBAL_POSITION_INT':
        #module_state.gps = [msg.lat,msg.lon]
        mpstate.autoland_state.update_gps(msg.lat,msg.lon)
        mpstate.autoland_state.update_alt(.001*msg.relative_alt)
        #module_state.alt = 0.001*msg.relative_alt#check units of this
    elif mtype == 'VFR_HUD':
        mpstate.autoland_state.update_aspeed(msg.airspeed)#check units, should be m/s
    elif mtype == 'ATTITUDE':
        mpstate.autoland_state.update_ahrs(msg.roll*57.30,msg.pitch*57.30,msg.yaw*57.30)#should be in deg      
