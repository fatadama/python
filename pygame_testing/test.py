import sys, pygame, numpy as np, math
from multiprocessing import Process, Pipe, Lock

#class to hold and manage data
class all_data:
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

class HUD:
    def __init__(self,conn = '',lock = ''):
        if (conn == ''):
            self._multiprocessing = 0
        else:
            self._multiprocessing = 1
        #use the lock and conn objects to get data from the main process
        if self._multiprocessing:
            self.conn = conn
            self.lock = lock
            self.lock.acquire()
        self._running = True
        pygame.init()
        #screen display properties
        self.size = (960,240)
        #HUD properties
        self.hudsize = (320,240)
        self.FOV_y = 30#degrees
        self.FOV_x = 40#degrees
        #topdown view properties
        self.topsize = (320,240)
        self.posHist = []#store the position history
        self._newPos = False#flag that is True when new GPS data are received
        #side view properties
        self.sidesize = (320,240)
        self.sidePos = []#store the position history
        self.background = (0,0,0)#black background
        self.screen = pygame.display.set_mode(self.size)
        self.screen.fill(self.background)
        #store all data messages here:
        self.data = all_data()
        #font object for text
        self.font = pygame.font.Font(None,30)
        
    def on_event(self, event):
        if event.type == pygame.QUIT:
            if self._multiprocessing:
                self.send_text('**.k.**')
                self.lock.release()
            self._running = False

    def on_loop(self):
        if self._running:
            if self._multiprocessing:
                self.check_data()
            else:
                pass
        else:
            pass

    def on_render(self):
        #reset display
        self.screen.fill(self.background)
    #render HUD with status text and orientation
        #render status text
        w,h = self.font.size("")
        string = "THETA: "+str(self.data.ahrs[1])
        self.render_text(string,(0,0),0,self.hudsize)
        string = "PHI: "+str(self.data.ahrs[0])
        self.render_text(string,(0,h),size=self.hudsize)
        string = "ALT: "+str(self.data.alt)
        self.render_text(string,(0,2*h),size=self.hudsize)
        string = "LAMBDA: %.2f" % self.data.lam
        self.render_text(string,(0,3*h),size=self.hudsize)
        string = "GAMMA: %.2f" % self.data.gam
        self.render_text(string,(0,4*h),size=self.hudsize)
        #transform the pitch axis
        offset = self.hudsize[0]*((self.data.ahrs[1] + math.degrees(math.atan(math.sqrt(self.data.alt)*.0002801)))/self.FOV_y)
        line_horizon = np.array([[0,0.5*self.hudsize[1]],[self.hudsize[0],0.5*self.hudsize[1]]]) + offset*np.array([[0,1],[0,1]])
        line_left = np.array([[0,0],[self.hudsize[0]*0.5,self.hudsize[1]*0.5]]) + offset*np.array([[0,1],[0,1]])
        line_right = np.array([[self.hudsize[0]*0.5,self.hudsize[1]*0.5],[self.hudsize[0],0]]) + offset*np.array([[0,1],[0,1]])
        #transform by roll:
        line_horizon = self.transform_roll(-self.data.ahrs[0],line_horizon,offset)
        line_left = self.transform_roll(-self.data.ahrs[0],line_left,offset)
        line_right = self.transform_roll(-self.data.ahrs[0],line_right,offset)
        #render visible attitude:
        #draw orientation lines
        self.render_line(line_left,(0,0,255))
        self.render_line(line_right,(0,0,255))
        #draw horizon line
        self.render_line(line_horizon,(0,255,0))
    #render top-down position and side view position
        #if not (self.posHist[0][0]==self.data.loc[0] && self.posHist[0][1]==self.data.loc):
        #update history
        self.render_text("X-Y",(self.hudsize[0],0),0)
        self.render_text("X: %.2f" % self.data.loc[0],(self.hudsize[0],h),0)
        self.render_text("Y: %.2f" % self.data.loc[1],(self.hudsize[0],2*h),0)
        self.render_line(np.array([[320,0],[320,240]]),(0,0,255),2)
        #draw the runway from (x = 100 to x = -100)
        self.render_line(np.array([[self.hudsize[0],self.topsize[1]*0.5],[self.hudsize[0]+200.0*self.topsize[0]/750.0,self.topsize[1]*0.5]]),(255,255,0),4)
        if self._newPos:
            self._newPos = False
            #calculate topdown position
            pos = np.array([100,0]) - self.data.loc[0:2]
            pos = pos*np.array([self.topsize[0]/750.0, self.topsize[1]/562.5])
            pos = pos + np.array([self.hudsize[0],self.topsize[1]*0.5])
            self.posHist.insert(0,(pos[0],pos[1]))
            #calculate sideview position
            self.sidePos.insert(0,(pos[0]+self.topsize[0],self.sidesize[1]-20-self.data.alt*self.sidesize[1]/562.5))
        #remove earliest value if more than 100 are stored
        if len(self.posHist)>250:
            self.posHist.pop()
            self.sidePos.pop()
            #transform: X = (100-x)*320/750
            #           Y = (281.25-y)*240/562.5
        #draw trajectory
        if len(self.posHist)>1:
            pygame.draw.lines(self.screen, (255,0,0), False, self.posHist,2)
    #render side view (glideslope) trajecory
        self.render_text("X-Z",(self.hudsize[0]+self.topsize[0],0),0)
        self.render_text("Z: %.2f" % -self.data.loc[2],(self.hudsize[0]+self.topsize[0],h),0)
        self.render_line(np.array([[640,0],[640,240]]),(0,0,255),2)
        #render runway
        self.render_line(np.array([[self.hudsize[0]+self.topsize[0],self.sidesize[1]-20],[self.hudsize[0]+self.topsize[0]+200*self.topsize[0]/750.0,self.sidesize[1]-20]]),(255,255,0),4)
        if len(self.sidePos)>1:
            pygame.draw.lines(self.screen, (255,0,0), False, self.sidePos,2)
        #write to display
        pygame.display.flip()

    def render_line(self,line,colorSpec=(255,0,0),thickness=2):
        pygame.draw.line(self.screen, colorSpec, (line[0,0],line[0,1]),(line[1,0],line[1,1]),thickness)

    def render_text(self,string,location=(0,0),centered=0,size=(320,240)):
        if centered:
            w,h = self.font.size(string)
            textIm = self.font.render(string,0,(255,255,255))
            self.screen.blit(textIm,(0.5*size[0]-w/2+location[0],size[1]-h+location[1]))#draw text
        else:
            textIm = self.font.render(string,0,(255,255,255))
            self.screen.blit(textIm,(location[0],location[1]))#draw text

    def transform_roll(self,phi,line,offset=0):
        phi = math.radians(phi)
        d = np.array([[1],[1]])*np.array([self.hudsize[0]*0.5,self.hudsize[1]*0.5+offset])
        line_init = line - d
        newline = np.dot(np.array([[math.cos(phi), math.sin(phi)],[-math.sin(phi), math.cos(phi)]]),line_init.transpose())
        newline = d + newline.transpose()
        return newline

    def on_execute(self):
        while(self._running):
            #process events - kill the program
            for event in pygame.event.get():
                self.on_event(event)
            #make computations
            self.on_loop()
            #draw to screen
            self.on_render()
        self.on_cleanup

    #send text to the main process
    def send_text(self,stringObj):
        if self._multiprocessing:
            self.conn.send(str(stringObj))
            return 1
        else:
            return 0

    #check if the main process has an update
    def check_data(self):
        self.send_text('**.u.**')
        self.lock.release()
        #allow main process to send data
        while self.conn.poll(0.05):
            message = self.conn.recv()
            if message[0] == 'gps':
                self.update_gps(message)
                self._newPos = True
                pass
            elif message[0] == 'ahrs':
                self.update_ahrs(message)
            elif message[0] == 'alt':
                self.update_alt(message)
            elif message[0] == 'aspeed':
                #self.update_aspeed(message)
                pass
        #re-acquire the lock and continue
        self.lock.acquire()

    def update_ahrs(self,message):
        self.data.update_ahrs(message[1],message[2],message[3])

    def update_alt(self,message):
        self.data.update_alt(message[1])

    def update_gps(self,message):
        self.data.update_gps(message[1],message[2])
            
    def on_cleanup():
        pygame.quit()
        sys.exit()

def run(conn,lock):
    App = HUD(conn,lock)
    App.on_execute()
            
if __name__ == "__main__":
    App = HUD()
    App.on_execute()
