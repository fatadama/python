import cv2, cv, numpy as np,time, pickle

hsv = np.array([])

def main():
    fname = "test_1.png"
    imageProc(fname)

def nothing(args):
    pass

def settingUpdate(blurRad):
    blurRad = cv2.getTrackbarPos('blur','camera')
    return

def selectXY(event,x,y,flags,param):
    global hsv
    if event == cv2.EVENT_LBUTTONDOWN:
        tarX = y
        tarY = x
        print y,x,hsv[y,x]
    if event == cv2.EVENT_RBUTTONDOWN:
        tarX = -1
        tarY = -1

def customRange(img,lower,upper):
    imgout = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    for i in range(0,np.size(img,0)):
        for j in range(0,np.size(img,1)):
            imgout[i,j] = ( (img[i,j,:] < upper).all() and (img[i,j,:] > lower).all() )*255
            if imgout[i,j] > 0:
                print i,j,img[i,j,:]
    return imgout


def imageProc(fname):
    global hsv
    
    #initialize variables for HSV limits and blur radius:
    blurRad = 3#image blur radius
    
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
        hsv = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
        #update settings from sliders:
        settingUpdate(blurRad)
        #process frames
        
        #blur the image to reduce color noise: (5 x 5)
        img = cv2.blur(img,(blurRad,blurRad))
        
        #img2 = np.zeros(np.shape(img))
        #img2 = OT.improcess(img)
        #cx,cy = int(OT.tarX),int(OT.tarY)
        #cv2.circle(img2,(cx,cy),3,(255,0,0),-1)

        hsvl = np.array([19,17,208])#lower HSV cutoff
        hsvu = np.array([31,143,255])#upper HSV cutoff

        if flagShowVis:
            cv2.imshow('camera',img)
        else:
            thresh = cv2.inRange(hsv,hsvl,hsvu)
            #thresh = customRange(hsv,hsvl,hsvu)
            #find contours in the thresholded image:
            #contours,hierarchy = cv2.findContours(thresh,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
            #pickle contours to deal with a bug in opencv 2.4.3
            #tmp = pickle.dumps(contours)
            #contours = pickle.loads(tmp)
            #cv2.drawContours(img,contours,-1,(255,255,255),-1)
            print thresh
            cv2.imshow('camera',thresh)
        
        keyRet = cv2.waitKey(5)
        #see if user hits 'ESC' in opencv windows
        if keyRet==27:
            break
        elif keyRet==32:
            flagShowVis = not flagShowVis
    cv2.destroyAllWindows()


if __name__=="__main__":
    main()
