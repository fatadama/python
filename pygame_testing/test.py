import sys, pygame, numpy as np, math
from multiprocessing import Process, Pipe, Lock

import message_objects as m_o

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
        #HUD properties
        self.size = (320,240)
        self.FOV_y = 30#degrees
        self.FOV_x = 40#degrees
        self.background = (0,0,0)#black background
        self.screen = pygame.display.set_mode(self.size)
        self.screen.fill((0,0,0))
        #store all data messages here:
        self.data = m_o.all_data()
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
        self.screen.fill((0,0,0))
        #render status text
        thetastr = "THETA: "+str(self.data.ahrs[1])
        self.render_text(thetastr,(0,0),centered=0)
        w,h = self.font.size("")
        self.render_text("PHI: "+str(self.data.ahrs[0]),(0,h))
        #transform the pitch axis:
        offset = self.size[0]*((self.data.ahrs[1] + math.degrees(math.atan(math.sqrt(self.data.alt)*.0002801)))/self.FOV_y)
        line_horizon = np.array([[0,0.5*self.size[1]],[self.size[0],0.5*self.size[1]]]) + offset*np.array([[0,1],[0,1]])
        line_left = np.array([[0,0],[self.size[0]*0.5,self.size[1]*0.5]]) + offset*np.array([[0,1],[0,1]])
        line_right = np.array([[self.size[0]*0.5,self.size[1]*0.5],[self.size[0],0]]) + offset*np.array([[0,1],[0,1]])
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
        #write to display
        pygame.display.flip()

    def render_line(self,line,colorSpec=(255,0,0),thickness=2):
        pygame.draw.line(self.screen, colorSpec, (line[0,0],line[0,1]),(line[1,0],line[1,1]),thickness)

    def render_text(self,string,location=(0,0),centered=0):
        if centered:
            w,h = self.font.size(string)
            textIm = self.font.render(string,0,(255,255,255))
            self.screen.blit(textIm,(0.5*self.size[0]-w/2+location[0],self.size[1]-h+location[1]))#draw text
        else:
            textIm = self.font.render(string,0,(255,255,255))
            self.screen.blit(textIm,(location[0],location[1]))#draw text

    def transform_roll(self,phi,line,offset=0):
        phi = math.radians(phi)
        d = np.array([[1],[1]])*np.array([self.size[0]*0.5,self.size[1]*0.5+offset])
        line_init = line - d
        newline = np.dot(np.array([[math.cos(phi), math.sin(phi)],[-math.sin(phi), math.cos(phi)]]),line_init.transpose())
        print np.array([[math.cos(phi), math.sin(phi)],[-math.sin(phi), math.cos(phi)]])
        print line_init.transpose()
        print newline
        print "\n"
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
                #self.update_gps(message)
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
            
    def on_cleanup():
        pygame.quit()
        sys.exit()

def run(conn,lock):
    App = HUD(conn,lock)
    App.on_execute()
            
if __name__ == "__main__":
    App = HUD()
    App.on_execute()
