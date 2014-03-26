import cv2, cv, numpy as np,time, pickle

def main():
    fname1 = "Easy Star Autoland.mp4"
    imageProc(fname1)

def nothing(args):
    pass

def settingUpdate(blurRad):
    blurRad = cv2.getTrackbarPos('blur','camera')
    return

def imageProc(fname):
    capture = cv2.VideoCapture(fname)
    
    #initialize variables for HSV limits and blur radius:
    blurRad = 5#image blur radius
    
    #load camera
    #print capture.get(cv.CV_CAP_PROP_FPS)
    frsize = (int(capture.get(cv.CV_CAP_PROP_FRAME_WIDTH)),int(capture.get(cv.CV_CAP_PROP_FRAME_HEIGHT)))
    vidWriter = cv2.VideoWriter("stabilized.wmv",cv.CV_FOURCC('M','J','P','G'),capture.get(cv.CV_CAP_PROP_FPS),frsize)
    print vidWriter

    first = True
    while True:
        ret,img1 = capture.read()
        if ret:
            #read the camera image:
            if first:
                first = False
            else:
                imgNew = cv2.cvtColor(img1,cv2.COLOR_BGR2GRAY)
                imgLast = cv2.cvtColor(img2,cv2.COLOR_BGR2GRAY)

                #process frames
                    
                #perform stabilization
                reet = cv2.phaseCorrelate(np.float32(imgNew),np.float32(imgLast))
                #shift the new image
                M = np.float32([[1,0,reet[0]],[0,1,reet[1]]])
                cols,rows = np.size(img1,axis=1),np.size(img1,axis=0)

                img3 = cv2.warpAffine(img2,M,(cols,rows))
                #export image
                vidWriter.write(img3)
            img2 = np.copy(img1)
        else:
            break

    if vidWriter.isOpened():
        vidWriter.release()

if __name__=="__main__":
    main()
