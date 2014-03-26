import cv2, cv, numpy as np,time, pickle

def main():
    fname = "test_1.png"
    imageProc(fname)

def nothing(args):
    pass

def settingUpdate(hsvL,hsvU,blurRad,rgbLim):
    hsvL[0] = cv2.getTrackbarPos('hLower','sliders1')
    hsvL[1] = cv2.getTrackbarPos('sLower','sliders1')
    hsvL[2] = cv2.getTrackbarPos('vLower','sliders1')
    #ensure that the upper bound is greater than the lower bound:
    hsvU[0] = np.amax(np.array([cv2.getTrackbarPos('hUpper','sliders1'),hsvL[0]+1]))
    hsvU[1] = np.amax(np.array([cv2.getTrackbarPos('sUpper','sliders1'),hsvL[1]+1]))
    hsvU[2] = np.amax(np.array([cv2.getTrackbarPos('vUpper','sliders1'),hsvL[2]+1]))
    blurRad = cv2.getTrackbarPos('blur','camera')
    rgbLim[0,0] = cv2.getTrackbarPos('rLower','sliders2')
    rgbLim[0,1] = cv2.getTrackbarPos('gLower','sliders2')
    rgbLim[0,2] = cv2.getTrackbarPos('bLower','sliders2')
    rgbLim[1,0] = cv2.getTrackbarPos('rUpper','sliders2')
    rgbLim[1,1] = cv2.getTrackbarPos('gUpper','sliders2')
    rgbLim[1,2] = cv2.getTrackbarPos('bUpper','sliders2')
    return

def imageProc(fname):
    
    #initialize variables for HSV limits and blur radius:
    blurRad = 3#image blur radius
    hsvl = np.array([19,17,208])#lower HSV cutoff
    hsvu = np.array([31,143,255])#upper HSV cutoff
    rgbLim = np.array([[122,190,219],[255,255,255]])#rgb lower/upper cutoffs
    
    #create trackbars for HSV limits and blur value:
    cv2.namedWindow('sliders1')
    cv2.namedWindow('sliders2')
    cv2.createTrackbar('hLower', 'sliders1', hsvl[0], 255, nothing)
    cv2.createTrackbar('sLower', 'sliders1', hsvl[1], 255, nothing)
    cv2.createTrackbar('vLower', 'sliders1', hsvl[2], 255, nothing)
    cv2.createTrackbar('hUpper', 'sliders1', hsvu[0], 255, nothing)
    cv2.createTrackbar('sUpper', 'sliders1', hsvu[1], 255, nothing)
    cv2.createTrackbar('vUpper', 'sliders1', hsvu[2], 255, nothing)
    cv2.createTrackbar('blur','camera',blurRad,15,nothing)

    cv2.createTrackbar('rLower', 'sliders2', rgbLim[0,0], 255, nothing)
    cv2.createTrackbar('gLower', 'sliders2', rgbLim[0,1], 255, nothing)
    cv2.createTrackbar('bLower', 'sliders2', rgbLim[0,2], 255, nothing)
    cv2.createTrackbar('rUpper', 'sliders2', rgbLim[1,0], 255, nothing)
    cv2.createTrackbar('gUpper', 'sliders2', rgbLim[1,1], 255, nothing)
    cv2.createTrackbar('bUpper', 'sliders2', rgbLim[1,2], 255, nothing)
    
    #load camera
    cv2.namedWindow('camera')#camera image
    
    flagShowVis = True
    while True:
        #read the camera image:
        #ret,img = capture.read()
        img = cv2.imread(fname)
        #update settings from sliders:
        settingUpdate(hsvl,hsvu,blurRad,rgbLim)
        #process frames
        
        #blur the image to reduce color noise: (5 x 5)
        img = cv2.blur(img,(blurRad,blurRad))
        img2 = np.copy(img)

        #filter the image in RGB space?
        thres = cv2.inRange(img,rgbLim[0,:],rgbLim[1,:])
        img2[thres==0]=0
        
        #convert image to HSV
        hsv = cv2.cvtColor(img2,cv2.COLOR_BGR2HSV)
        #threshold the image using the HSV lower and upper bounds
        thresh = cv2.inRange(hsv,hsvl,hsvu)
        #find contours in the thresholded image:
        contours,hierarchy = cv2.findContours(thresh,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
        
        #pickle contours to deal with a bug in opencv 2.4.3
        tmp = pickle.dumps(contours)
        contours = pickle.loads(tmp)
        
        #get the contour with the largest area:
        max_area = -1
        best_cnt = np.array([])
        cx,cy = (0,0)

        #loop over the contours and find the one with the largest area:
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area>50:
                if area>max_area:
                    max_area = area
                    best_cnt = cnt
                    
        #check that the size of the best contour is not empty
        if np.shape(best_cnt)[0]>0:
            #find the centroid of best contour
            M = cv2.moments(best_cnt)
            #check that the divisor moment is nonzero; if it is, set the location to (0,0)
            if M['m00']>0:
                cx,cy = int(M['m10']/M['m00']),int(M['m01']/M['m00'])
            else:
                cx,cy = (0,0)
        if flagShowVis:
            #draw circle at contour centroid:
            cv2.circle(img,(cx,cy),3,(0,255,0),-1)
            cv2.imshow('camera',img)
        else:
            #try drawing the best contour and not showing the thresholded image
            cv2.circle(img,(cx,cy),3,(0,255,0),-1)
            cv2.drawContours(img,contours,-1,(255,255,255),-1)
            cv2.imshow('camera',img)
        keyRet = cv2.waitKey(5)
        #see if user hits 'ESC' in opencv windows
        if keyRet==27:
            break
        elif keyRet==32:
            flagShowVis = not flagShowVis
    cv2.destroyAllWindows()


if __name__=="__main__":
    main()
