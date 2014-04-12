import cv2, cv, numpy as np,time, pickle, binarySearch as bs, os

#called from mavproxy when 'camera' is entered into the console.
#when runCameraProc is called, it initializes the camera streaming window and trackbars
#   that control the thresholding for HSV filtering. Image is HSV filtered and the largest
#   resulting contour is centroided. A moving average of centroids is maintained until mavproxy
#   requests an update, which should occur at 1 Hz. The average centroid is then used to
#   look up the appropriate action in the Q-matrix.
#
#development progress: currently, q-matrix has not been implemented.

#set to 1 for debugging only, no q-lookup
DEBUG = 0

def nothing(args):
    pass

def settingUpdate(hsvL,hsvU,blurRad):
    hsvL[0] = cv2.getTrackbarPos('hLower','sliders')
    hsvL[1] = cv2.getTrackbarPos('sLower','sliders')
    hsvL[2] = cv2.getTrackbarPos('vLower','sliders')
    #ensure that the upper bound is greater than the lower bound:
    hsvU[0] = np.amax(np.array([cv2.getTrackbarPos('hUpper','sliders'),hsvL[0]+1]))
    hsvU[1] = np.amax(np.array([cv2.getTrackbarPos('sUpper','sliders'),hsvL[1]+1]))
    hsvU[2] = np.amax(np.array([cv2.getTrackbarPos('vUpper','sliders'),hsvL[2]+1]))
    blurRad = cv2.getTrackbarPos('blur','sliders')
    return

def runCameraProc(conn,lock,flag_testing=False):
    global rollHist
    #flag_testing is passed as True to skip over any connection/lock stuff
    #tell main that the process is running:
    if not flag_testing:
        conn.send('**.online.**')
        #acquire lock
        lock.acquire()
    
    #initialize variables for HSV limits and blur radius:
    blurRad = 5#image blur radius
    hsvl = np.array([19,17,208])#lower HSV cutoff
    hsvu = np.array([31,143,255])#upper HSV cutoff
    rgbLim = np.array([[122,190,219],[255,255,255]])#rgb lower/upper cutoffs - THESE ARE NOT ADJUSTABLE ON-LINE!!

    #numFrames: the number of frames processed in the current moving average calculation
    numFrames = 0
    #cxbar, cybar: average centroid location in the frame
    [cxbar,cybar] = [0,0]
    #numBanks: the number of bank angles received from the aircraft (degrees) for moving average calculation
    numBanks = 0
    #phibar: the moving average bank angle, (deg)
    phibar = 0
    #ACTION: the action to take. is +/-2, 0
    action = 0
    #t_last: the last time a command was sent from MAVProxy. If this is more than 10? seconds, release the lock for 0.5 seconds, in case MAVProxy main() has got stuck waiting to  acquire lock.
    t_last = time.clock()
    #create trackbars for HSV limits and blur value:
    cv2.namedWindow('sliders')
    cv2.createTrackbar('hLower', 'sliders', hsvl[0], 255, nothing)
    cv2.createTrackbar('sLower', 'sliders', hsvl[1], 255, nothing)
    cv2.createTrackbar('vLower', 'sliders', hsvl[2], 255, nothing)
    cv2.createTrackbar('hUpper', 'sliders', hsvu[0], 255, nothing)
    cv2.createTrackbar('sUpper', 'sliders', hsvu[1], 255, nothing)
    cv2.createTrackbar('vUpper', 'sliders', hsvu[2], 255, nothing)
    
    #load camera
    cv2.namedWindow('camera')#camera image
    cv2.createTrackbar('blur','camera',blurRad,15,nothing)
    #capture = cv2.VideoCapture(0)
    capture = cv2.VideoCapture("../pass3.mpg")

    #add a new trackbar to trigger video logging on/off
    cv2.createTrackbar('record','camera',0,1,nothing)
    
    #open video writer for later use
    i = 1
    fname = 'rec' + str(i) +'.avi'
    for name in os.listdir('.'):
        if name == fname:
            i = i+1
            fname = 'rec' + str(i) +'.avi'
    frsize = (int(capture.get(cv.CV_CAP_PROP_FRAME_WIDTH)),int(capture.get(cv.CV_CAP_PROP_FRAME_HEIGHT)))
    vidWriter = cv2.VideoWriter(fname,cv.CV_FOURCC('M','J','P','G'),20,frsize)
    print vidWriter
    #open text log that corresponds to the video
    vidLog = open(fname[0:-3]+'log','w')
    #open Q-matrix log. format name is 'qLog##.log', where ## is the same as in 'fname':
    qLog = open('qLog'+fname[3:-4]+'.log','w')
    qLog.write('time(sec),c_x(float),c_y(float),phi(float),c_x(px),c_y(px),phi(deg/int),action(int)\n')

    # if we are loading a roll history file for debugging, verify with rollHist.size > 1
    FLAG_ROLLHIST = False
    if rollHist.size > 1:
        FLAG_ROLLHIST = True
    
    #variable that governs if video is being written:
    flag_writing = 0
    
    #open the Q-matrix
    Qtable = bs.load_Q()

    # track the time for using the roll history
    time1 = 0.0
    timeLastLookup = -100.0#the time of the last q-lookup
    lookuprate_Hz = 1
    inNow = [np.array([])]
    
    if not capture.isOpened:
        print "****Error: camera not found****"
    else:
        print capture
        flagShowVis = True
        while True:
            if FLAG_ROLLHIST:
                if inNow[0].size > 1:
                    inLast = np.copy(inNow[0])
                else:
                    inLast = np.array([])
            #read the camera image:
            ret,img = capture.read()
            if ret:
                #update settings from sliders:
                settingUpdate(hsvl,hsvu,blurRad)
                flag_writing = cv2.getTrackbarPos('record','camera')
                if not DEBUG:
                #process frames
                    
                    #blur the image to reduce color noise: (5 x 5)
                    img = cv2.blur(img,(blurRad,blurRad))

                    #filter the image in RGB space
                    thres = cv2.inRange(img,rgbLim[0,:],rgbLim[1,:])

                    #convert image to HSV
                    hsv = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
                    #threshold the image using the HSV lower and upper bounds
                    thresh = cv2.inRange(hsv,hsvl,hsvu)
                    ##thresh2 = np.copy(thresh)
                    #unionize the HSV and RGB thresholds:
                    thresh = thresh&thres
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
                else:
                    contours = np.array([0])
                    cx,cy = (0,0)
                    
                #update the moving averages:
                if cx>0 and cy>0:
                    #ensure that cx>0, cy>0 in case centroid drops out
                    numFrames = numFrames+1
                    cxbar = (cx+cxbar*(numFrames-1.0))/numFrames
                    cybar = (cy+cybar*(numFrames-1.0))/numFrames
                #if recording, add "RECORDING" to VISIBLE image only
                if flag_writing==1:
                    img2 = np.copy(img)
                    cv2.putText(img,'RECORDING',(0,25),cv2.FONT_HERSHEY_DUPLEX,1,(0,0,255),thickness=2)
                    #write to VideoWriter
                    if np.shape(best_cnt)[0]>0:
                        cv2.drawContours(img2,best_cnt,-1,(255,0,0),2)
                        #write time, centroid location to file
                        vidLog.write(str(time.clock())+','+str(cx)+','+str(cy)+'\n')
                    vidWriter.write(img2)                    
                if flagShowVis:
                    #draw circle at contour centroid:
                    cv2.circle(img,(cx,cy),3,(0,255,0),-1)
                    cv2.imshow('camera',img)
                else:
                    #draw the contours on the true color image:
                    cv2.circle(img,(cx,cy),3,(0,255,0),-1)
                    cv2.drawContours(img,contours,-1,(255,0,0),2)
                    cv2.imshow('camera',img)
                    ##cv2.circle(thresh2,(cx,cy),3,(0,255,0),-1)
                    ##cv2.imshow('camera',thresh2)
            time.sleep(.01)

            time1 += .05
                    
            keyRet = cv2.waitKey(5)
            #see if user hits 'ESC' in opencv windows
            if keyRet==27:
                break
            elif keyRet==32:
                flagShowVis = not flagShowVis
            #see if mavproxy has sent a command
            if not flag_testing:
                if conn.poll(0.05):
                    t_last = time.clock()
                    #if a command comes, process it
                    #   **.kill.** - terminate process and close all windows
                    #   **.update.** - transmit current [cx,cy] to the main process and reset the average
                    #   **.bank.** - this is followed by the current MAV bank angle (deg)
                    recvVal = conn.recv()
                    if recvVal == '**.kill.**':
                        break
                    elif recvVal == '**.update.**':
                        #use cxbar, cybar, phibar to compute the appropriate bank angle.
                        #log the "raw" time and state info
                        qLog.write(str(time.clock())+','+str(cxbar)+','+str(cybar)+','+str(phibar)+',')
                        
                        #round phibar to the nearest 2 degrees:
                        phibar = int(np.floor(phibar))
                        phibar = phibar+phibar%2
                        #round cxbar and cybar to the appropriate ranges: don't know these
                        #y-axis is spaced every 24 px starting at 7
                        cybar = int((cybar-7)/24)*24+7
                        #x-axis every 24 px starting at 0
                        cxbar = int(cxbar/24)*24

                        #lookup action in Q-matrix
                        action = bs.qFind(Qtable,[cxbar,cybar,phibar])
                        #Transmit the target bank angle, which is the bank angle rounded to 2 degrees plus the actions;
                        #   return -2 (decrease bank angle),0 (do nothing),2 (increase bank angle)
                        #check that the current state is found in the q-matrix: if not, do not change actions
                        if action == -10:
                            print 'Could not match states in Q-matrix'
                            action = 0
                        #check that bank angle limits are not exceeded:
                        if phibar>=30 and action==2:
                            action = 0
                        if phibar<=-30 and action==-2:
                            action = 0
                        #send the action
                        conn.send(action+phibar)

                        lock.release()#release the lock so main can grab the data from the pipe

                        #log the rounded cxbar, cybar, phibar, and the commanded action:
                        qLog.write(str(cxbar)+','+str(cybar)+','+str(phibar)+','+str(action)+'\n')
                        
                        #reset cxbar, cybar
                        numFrames = 0
                        [cxbar,cybar] = [0,0]
                        #reset phibar, numBanks
                        numBanks = 0
                        phibar = 0
                        
                        lock.acquire()#wait until main is done getting the data, then re-acquire the lock
                    elif recvVal == '**.bank.**':
                        #release lock
                        lock.release()
                        #read in bank angle from process:
                        if conn.poll(0.05):
                            #update moving average calculation
                            numBanks = numBanks+1
                            phi = conn.recv()
                            phibar = (phi+phibar*(numBanks-1))/numBanks
                        else:
                            print 'camProcess did not receive bank angle from MAVProxy'
                        #acquire lock
                        lock.acquire()
                if ((t_last-time.clock())>10):
                    print 'camProcess releasing lock to try to restart main'
                    lock.release()
                    time.sleep(0.5)
                    lock.acquire()
            else:
                # if we are testing, still check and see if we are debugging using an established roll history
                if FLAG_ROLLHIST:
                    #find the first time index that is less than the current time, time1
                    inNow=np.nonzero( rollHist[0,:,0] <= time1 )
                    if inNow[0].size > 1:
                        if inLast.size > 1:
                            if (not np.all(inNow[0]==inLast)):
                                #get the current bank angle
                                numBanks = numBanks+1
                                phi = 180.0/3.14159*rollHist[0,inNow[0][-1],1]#convert to degrees
                                phibar = (phi+phibar*(numBanks-1))/numBanks
                        else:
                            numBanks = numBanks+1
                            phi = rollHist[0,inNow[0][-1],1]
                            phibar = (phi+phibar*(numBanks-1))/numBanks
                    if (time1 - timeLastLookup) > 1./lookuprate_Hz:
                        timeLastLookup = time1
                        #do the q-lookup - copied all this from the normal process above, inelegant but will work
                        #use cxbar, cybar, phibar to compute the appropriate bank angle.
                        #log the "raw" time and state info
                        qLog.write(str(time1)+','+str(cxbar)+','+str(cybar)+','+str(phibar)+',')
                        
                        #round phibar to the nearest 2 degrees:
                        phibar = int(np.floor(phibar))
                        phibar = phibar+phibar%2
                        #round cxbar and cybar to the appropriate ranges: don't know these
                        #y-axis is spaced every 24 px starting at 7
                        cybar = int((cybar-7)/24)*24+7
                        #x-axis every 24 px starting at 0
                        cxbar = int(cxbar/24)*24

                        #lookup action in Q-matrix
                        action = bs.qFind(Qtable,[cxbar,cybar,phibar])
                        #Transmit the target bank angle, which is the bank angle rounded to 2 degrees plus the actions;
                        #   return -2 (decrease bank angle),0 (do nothing),2 (increase bank angle)
                        #check that the current state is found in the q-matrix: if not, do not change actions
                        if action == -10:
                            print 'Could not match states in Q-matrix'
                            action = 0
                        #check that bank angle limits are not exceeded:
                        if phibar>=30 and action==2:
                            action = 0
                        if phibar<=-30 and action==-2:
                            action = 0
                        print time1,phibar,action
                        #log the rounded cxbar, cybar, phibar, and the commanded action:
                        qLog.write(str(cxbar)+','+str(cybar)+','+str(phibar)+','+str(action)+'\n')
                        
                        #reset cxbar, cybar
                        numFrames = 0
                        [cxbar,cybar] = [0,0]
                        #reset phibar, numBanks
                        numBanks = 0
                        phibar = 0
                    
    cv2.destroyAllWindows()
    if not flag_testing:
        conn.send("cam off")        
        conn.close()
        lock.release()
    #close recording file if still open:
    if vidWriter.isOpened():
        vidWriter.release()
        #move the video file to the archive folder:
    #close the video log:    
    vidLog.close()
    #close the q-matrix log
    qLog.close()

rollHist = np.array([])

if __name__ == "__main__":
    global rollHist
    #load rollOutput.txt roll history at a specified input
    time0 = raw_input('Specify the initial time index in rollOutput.txt:')
    time0 = long(time0)#convert to integer
    print('Initial time specified as t = ' + str(time0))
    # load file
    fin = open('rollOutput.txt','r+')
    data = np.zeros((1e5,4))
    datacount = 0
    while 6 > 5:
        line = fin.readline()
        if len(line) < 1:
            fin.close()
            break
        #split with spaces:
        lineSpl = line.split('\t')
        data[datacount,0] = float(lineSpl[0])
        for i in range(2):
            data[datacount,i+1] = float(lineSpl[i+1])
        data[datacount,3] = float(lineSpl[i+1][0:-1])
        datacount+=1
    #subtract the lowest time index
    data[0:datacount,0] = data[0:datacount,0] - np.tile([np.min(data[0:datacount,0])],(datacount,1)).transpose()
    #convert to seconds
    data[0:datacount,0] = .001*data[0:datacount,0]
    #get hte array of values to keep. assume no more than 50 seconds of footage
    keepind = np.nonzero(np.logical_and(data[0:datacount,0] >= time0,data[0:datacount,0] <=time0+50))
    rollHist = np.copy(data[keepind,0:2])
    rollHist[0,:,0] = rollHist[0,:,0]-247
    runCameraProc(True,True,True)
