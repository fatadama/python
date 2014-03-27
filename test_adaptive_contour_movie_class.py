import cv2, cv, numpy as np,time, pickle

tarX = -1
tarY = -1

class objectTracker():
    def __init__(self):
        self.tarX = -1
        self.tarY = -1
        self.lower = np.array([0,0,0])
        self.upper = np.array([255,255,255])
        self.gotObj = 0
        self.firstCall = 1
    def getXY(self,x,y):
        self.tarX = x
        self.tarY = y
        if x != -1:
            self.gotObj = 1
            self.firstCall = 1
        else:
            print "Resetting image processing"
            self.gotObj = 0
    def improcess(self,img):
        if self.gotObj:
            imgout = np.copy(img)
            #process image
            #get the local HSV estimate:
            hsv = cv2.cvtColor(imgout,cv2.COLOR_BGR2HSV)
            #if the first call, get the upper and lower bounds
            if self.firstCall:
                self.firstCall = 0
                xyhsv = hsv[self.tarY,self.tarX]
                self.lower = xyhsv
                self.upper = xyhsv
                #find adjacent pixels, say 10? to create a threshold
                #5,0.2 works well
                irange = range( max(self.tarX-5,0), min(self.tarX+5,480))
                jrange = range( max(self.tarY-5,0), min(self.tarY+5,640))
                for i in irange:
                    for j in jrange:
                        #print np.diff([hsv[i,j],xyhsv],axis=0 ),np.size(np.nonzero(np.diff([hsv[i,j],xyhsv],axis=0 ) < 50),1)
                        if np.amax( np.diff([hsv[i,j],xyhsv],axis=0 ) ) < 50:
                            self.lower = np.amin([self.lower,hsv[j,i]],axis=0)
                            self.upper = np.amax([self.upper,hsv[j,i]],axis=0)
                self.lower = self.lower-0.05*np.array([255,255,255])
                self.upper = self.upper+0.05*np.array([255,255,255])
            #threshold the image
            thresh = cv2.inRange(hsv,self.lower,self.upper)
            #get the contours
            contours,hierarchy = cv2.findContours(thresh,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
            #pickle contours to deal with a bug in opencv 2.4.3
            tmp = pickle.dumps(contours)
            contours = pickle.loads(tmp)
            #find the centroid closest to the target location:
            cmin = np.array([])
            cx,cy = (0,0)
            for cnt in contours:
                M = cv2.moments(cnt)
                #check that the divisor moment is nonzero; if it is, set the location to (0,0)
                if M['m00']>0:
                    ccx,ccy = int(M['m10']/M['m00']),int(M['m01']/M['m00'])
                else:
                    ccx,ccy = (0,0)
                if (pow(cx-self.tarX,2)+pow(cy-self.tarY,2) > pow(ccx-self.tarX,2)+pow(ccy-self.tarY,2)):
                    cx,cy = ccx,ccy
                    cmin = cnt
            #lowpass filter the target location using cx, cy
            alph = 0.35
            TC = 0.333333*(1.0-alph)/alph
            self.tarX = alph*cx + (1-alph)*self.tarX
            self.tarY = alph*cy + (1-alph)*self.tarY
            #self.tarX = cx
            #self.tarY = cy

            if not (type(cmin) is int):
                cv2.drawContours(imgout,cmin,-1,(0,0,0),2)
                #cv2.drawContours(imgout,contours,-1,(255,255,255),-1)
            # update upper and lower to match the contour
            if np.size(cmin,0) > 0:
                cnvxhll = cv2.convexHull(cmin)
                # need to lowpas these as well to not change too fast
                lowertemp = np.copy(self.lower)
                uppertemp = np.copy(self.upper)
                for i in range(0,np.size(cnvxhll,0)):
                    lowertemp= np.amin([self.lower,hsv[cnvxhll[i,0,1],cnvxhll[i,0,0]]],axis=0)
                    uppertemp = np.amax([self.upper,hsv[cnvxhll[i,0,1],cnvxhll[i,0,0]]],axis=0)
                self.lower = alph*lowertemp + (1-alph)*self.lower
                self.upper = alph*uppertemp + (1-alph)*self.upper
                print self.lower,self.upper
            return imgout
        else:
            return img

def main():
    fname = "pass3.mpg"
    imageProc(fname)

def nothing(args):
    pass

def settingUpdate(blurRad):
    blurRad = cv2.getTrackbarPos('blur','camera')
    return

def selectXY(event,x,y,flags,param):
    global OT
    if event == cv2.EVENT_LBUTTONDOWN:
        tarX = x
        tarY = y
        OT.getXY(x,y)
    if event == cv2.EVENT_RBUTTONDOWN:
        tarX = -1
        tarY = -1
        OT.getXY(-1,-1)

OT = objectTracker()

def imageProc(fname):
    global OT

    capture = cv2.VideoCapture(fname)
    
    #initialize variables for HSV limits and blur radius:
    blurRad = 10#image blur radius
    
    #create trackbars for HSV limits and blur value:
    cv2.createTrackbar('blur','camera',blurRad,15,nothing)
    
    #load camera
    cv2.namedWindow('camera')#camera image
    cv2.setMouseCallback('camera',selectXY)

    paused = False
    
    flagShowVis = True
    while True:
        #read the camera image:
        if not paused:
            ret,img = capture.read()
            #update settings from sliders:
            settingUpdate(blurRad)
            #process frames
            if ret:
                #blur the image to reduce color noise: (5 x 5)
                img = cv2.blur(img,(blurRad,blurRad))
                
                #img2 = np.zeros(np.shape(img))
                img2 = OT.improcess(img)
                cx,cy = int(OT.tarX),int(OT.tarY)
                cv2.circle(img2,(cx,cy),3,(255,0,0),-1)
                
                cv2.imshow('camera',img2)
        
        keyRet = cv2.waitKey(5)
        #see if user hits 'ESC' in opencv windows
        if keyRet==27:
            break
        elif keyRet==32:
            paused = not paused
    cv2.destroyAllWindows()


if __name__=="__main__":
    main()
