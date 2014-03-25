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
        tarX = x
        tarY = y
        if x != -1:
            self.gotObj = 1
            self.firstCall = 1
        else:
            self.gotObj = 0
    def improcess(self,img,coords,imgout):
        if self.gotObj:
            imgout = np.copy(img)
            #process image
            #if the first call, get the upper and lower bounds
            if self.firstCall:
                self.firstCall = 0
                #get the local HSV estimate:
                hsv = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
            
                xyhsv = hsv[self.tarX,self.tarY]
                lower = xyhsv
                upper = xyhsv
                #find adaject pixels, say 10? to create a threshold
                for i in range ((self.tarX-5),(self.tarX+5)):
                    for j in range (self.tarY-5,self.tarY+5):
                        if np.amax( np.diff([hsv[i,j],xyhsv],axis=0 ) ) < 5:
                            self.lower = np.amin([self.lower,hsv[i,j]],axis=0)
                            self.upper = np.amax([self.upper,hsv[i,j]],axis=0)
                self.lower = self.lower-0.3*np.array([255,255,255])
                self.upper = self.upper+0.3*np.array([255,255,255])
            #threshold the image
            thresh = cv2.inRange(hsv,lower,upper)
            #get the contours
            contours,hierarchy = cv2.findContours(thresh,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
            #find the centroid closest to the target location:
            cmin = 0
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
            self.tarX = cx
            self.tarY = cy
            
            coords = (self.tarX,self.tarY)

            if cmin.any():
                cv2.drawContours(imgout,cmin,-1,(0,0,0),2)
                #cv2.drawContours(img2,contours,-1,(255,255,255),-1)
                cv2.circle(imgout,(cx,cy),3,(255,0,0),-1)
            # update upper and lower to match the contour
            cnvxhll = cv2.convexHull(cnt)
            for i in range(0,np.size(cnvxhll,0)):
                self.lower = np.amin([self.lower,hsv[cnvxhll[i,0,1],cnvxhll[i,0,0]]],axis=0)
                self.upper = np.amax([self.upper,hsv[cnvxhll[i,0,1],cnvxhll[i,0,0]]],axis=0)
            
        else:
            imgout = img
            coords = (0,0)

def main():
    fname = "test_1.png"
    imageProc(fname)

def nothing(args):
    pass

def settingUpdate(blurRad):
    blurRad = cv2.getTrackbarPos('blur','camera')
    return

def selectXY(event,x,y,flags,param):
    global tarX,tarY
    if event == cv2.EVENT_LBUTTONDBLCLK:
        tarX = x
        tarY = y
    if event == cv2.EVENT_RBUTTONDOWN:
        tarX = -1
        tarY = -1

def imageProc(fname):
    global tarX,tarY
    
    #initialize variables for HSV limits and blur radius:
    blurRad = 5#image blur radius
    
    #create trackbars for HSV limits and blur value:
    cv2.createTrackbar('blur','camera',blurRad,15,nothing)
    
    #load camera
    cv2.namedWindow('camera')#camera image
    cv2.setMouseCallback('camera',selectXY)
    
    flagShowVis = True
    while True:
        #read the camera image:
        #ret,img = capture.read()
        img = cv2.imread(fname)
        #update settings from sliders:
        settingUpdate(blurRad)
        #process frames
        
        #blur the image to reduce color noise: (5 x 5)
        img = cv2.blur(img,(blurRad,blurRad))
        
        cv2.imshow('camera',img)
        if tarX is not -1 and tarY is not -1:
            #convert to HSV
            img2 = np.copy(img)
            hsv = cv2.cvtColor(img2,cv2.COLOR_BGR2HSV)
            
            xyhsv = hsv[tarX,tarY]
            lower = xyhsv
            upper = xyhsv
            #find adjacent pixels, say 10? to create a threshold
            for i in range ((tarX-5),(tarX+5)):
                for j in range (tarY-5,tarY+5):
                    if np.amax( np.diff([hsv[i,j],xyhsv],axis=0 ) ) < 5:
                        lower = np.amin([lower,hsv[i,j]],axis=0)
                        upper = np.amax([upper,hsv[i,j]],axis=0)
            lower = lower-0.3*np.array([255,255,255])
            upper = upper+0.3*np.array([255,255,255])
            print lower,upper
            thresh = cv2.inRange(hsv,lower,upper)
            contours,hierarchy = cv2.findContours(thresh,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
            cmin = 0
            cx,cy = (0,0)
            for cnt in contours:
                M = cv2.moments(cnt)
                #check that the divisor moment is nonzero; if it is, set the location to (0,0)
                if M['m00']>0:
                    ccx,ccy = int(M['m10']/M['m00']),int(M['m01']/M['m00'])
                else:
                    ccx,ccy = (0,0)
                if (pow(cx-tarX,2)+pow(cy-tarY,2) > pow(ccx-tarX,2)+pow(ccy-tarY,2)):
                    cx,cy = ccx,ccy
                    cmin = cnt
            
            #print contours
            if cmin.any():
                cv2.drawContours(img2,cmin,-1,(0,0,0),2)
                #cv2.drawContours(img2,contours,-1,(255,255,255),-1)
                cv2.circle(img2,(cx,cy),3,(255,0,0),-1)
            cv2.imshow('camera',img2)
            # update upper and lower to match the contour
            cnvxhll = cv2.convexHull(cmin)
            for i in range(0,np.size(cnvxhll,0)):
                lower = np.amin([lower,hsv[cnvxhll[i,0,1],cnvxhll[i,0,0]]],axis=0)
                upper = np.amax([upper,hsv[cnvxhll[i,0,1],cnvxhll[i,0,0]]],axis=0)
            
        keyRet = cv2.waitKey(5)
        #see if user hits 'ESC' in opencv windows
        if keyRet==27:
            break
        elif keyRet==32:
            flagShowVis = not flagShowVis
    cv2.destroyAllWindows()


if __name__=="__main__":
    main()
