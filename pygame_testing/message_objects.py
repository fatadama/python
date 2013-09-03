#define message objects

import math

class all_data:
    def __init__(self):
        self.gps = [0,0]#lat, long
        self.ahrs = [0,0,0]#roll,pitch,yaw
        self.aspeed = 0
        self.alt = 0#altitude (m)
        self.lam = 0#localizer angle
        self.gam = 0#glideslope angle
        self.loc = [0,0,0]#postiion vector in runway-centric coords
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

class gps_msg:
    def __init__(self):
        self.lat = []
        self.lon = []
        self.type = 'gps'
    def get_lat(self):
        return self.lat
    def get_lon(self):
        return self.lon
    def update_lat(self,argin):
        self.lat = argin
    def update_lon(self,argin):
        self.lon = argin
    def update(self,argin1,argin2):
        self.lat = argin1
        self.lon = argin2

class ahrs_msg:
    def __init__(self):
        self.roll = []
        self.yaw = []
        self.pitch = []
        self.type = 'ahrs'
    def get_roll(self):
        return self.roll
    def get_pitch(self):
        return self.pitch
    def get_yaw(self):
        return self.yaw
    def update(self, psi, theta, phi):
        self.yaw = psi
        self.pitch = theta
        self.roll = phi

class alt_msg:
    def __init__(self):
        self.alt = []
        self.type = 'alt'
    def get_alt(self):
        return self.alt
    def update(self,argin):
        self.alt = argin

class aspeed_msg:
    def __init__(self):
        self.aspeed = []
        self.type = 'aspeed'
    def get_aspeed(self):
        return self.aspeed
    def update(self,argin):
        self.aspeed = argin
