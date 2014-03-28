#/usr/bin/env python

'''
This sample demonstrates Canny edge detection.

Usage:
  edge.py [<video source>]

  Trackbars control edge thresholds.

'''

import cv2
#import video
import sys
import numpy as np
import pickle

def selectXY(event,x,y,flags,param):
    # mouse X-Y is image from Y-X
    global tarX,tarY, flag_click
    if event == cv2.EVENT_LBUTTONDOWN:
        flag_click = True
        tarX = x
        tarY = y
    if event == cv2.EVENT_RBUTTONDOWN:
        flag_click = False
        tarX = -1
        tarY = -1

tarX,tarY = -1,-1

if __name__ == '__main__':
    print __doc__

    global tarX,tarY
    flag_click = False

    try: fn = sys.argv[1]
    except: fn = 0

    def nothing(*arg):
        pass

    # on an X-Y click, try to find the smallest convex polygon near the XY click
    # use binary search to figure out the approximate radius in X-Y space??

    cv2.namedWindow('edge')
    cv2.setMouseCallback('edge',selectXY)
    cv2.createTrackbar('thrs1', 'edge', 2375, 5000, nothing)
    cv2.createTrackbar('thrs2', 'edge', 750, 5000, nothing)

    #cap = video.create_capture(fn)
    img = cv2.imread('test_1.png')
    while True:
        if not flag_click:
            img = cv2.imread('test_1.png')
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            thrs1 = cv2.getTrackbarPos('thrs1', 'edge')
            thrs2 = cv2.getTrackbarPos('thrs2', 'edge')
            edge = cv2.Canny(gray, thrs1, thrs2, apertureSize=5)
            vis = img.copy()
            vis /= 2
            vis[edge != 0] = (0, 255, 0)
        
        if flag_click:
            print "Searching for edges"
            #process image to find X-Y bounds of edges
            #search upwards
            edgeind = np.nonzero(np.array(edge > 0))
            sides = [[0,0],[0,0],[0,0],[0,0]]
            flags = [False,False,False,False]
            for i in range(1,20):
                if not flags[0] and (np.sum(np.array(edgeind <= np.tile([[tarY],[tarX+i]],(1,np.size(edgeind,1)))) & np.array(edgeind >= np.tile([[tarY],[tarX]],(1,np.size(edgeind,1)))),0)>1).any():
                    sides[0][0],sides[0][1] = tarY,tarX+i
                    flags[0] = True
                if not flags[2] and (np.sum(np.array(edgeind >= np.tile([[tarY],[tarX-i]],(1,np.size(edgeind,1)))) & np.array(edgeind <= np.tile([[tarY],[tarX]],(1,np.size(edgeind,1)))),0)>1).any():
                    #sides[2,:] = [tarY,tarX-i]
                    sides[2][0],sides[2][1] = tarY,tarX-i
                    flags[2] = True
                if not flags[1] and (np.sum(np.array(edgeind <= np.tile([[tarY+i],[tarX]],(1,np.size(edgeind,1)))) & np.array(edgeind >= np.tile([[tarY],[tarX]],(1,np.size(edgeind,1)))),0)>1).any():
                    #sides[1,:] = [tarY+i,tarX]
                    sides[1][0],sides[1][1] = tarY+i,tarX
                    flags[1] = True
                if not flags[3] and (np.sum(np.array(edgeind >= np.tile([[tarY-i],[tarX]],(1,np.size(edgeind,1)))) & np.array(edgeind <= np.tile([[tarY],[tarX]],(1,np.size(edgeind,1)))),0)>1).any():
                    #sides[3,:] = [tarY-i,tarX]
                    sides[3][0],sides[3][1] = tarY-i,tarX
                    flags[3] = True
                if all(flags):
                    break
            if sum(flags)<4:
                for i in range(0,4):
                    if not flags[i]:
                        sides[i][:] = [tarY,tarX]
            # look at the window bounded by the identified points +5% - fit an ellipse and take the properties
            # want a best fit to the four points for maximum area, but a naive fit will do
            #semimajor and semiminor axes:
            a = 0.5*(sides[1][0]-sides[3][0])
            b = 0.5*(sides[2][1]-sides[0][1])
            inds = np.zeros((0,2)).astype(int)
            for i in range(sides[3][0],sides[1][0]):
                for j in range(sides[2][1],sides[0][1]):
                    if (pow((i-tarY)/a,2) + pow((j-tarX)/b,2)) <= 1:
                        inds = np.vstack((inds,[i,j]))
            
            #print (int(sides[0,1]),int(sides[1,0])),(int(sides[2,1]),int(sides[3,0]))
            #cv2.rectangle(vis,(int(sides[0][1]),int(sides[1][0])),(int(sides[2][1]),int(sides[3][0])),(127,255,127),-1)
            # find points in the rectangle and threshold in HSV space            
            hsv = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
            hsvsub = hsv[inds[:,0],inds[:,1]]
            #lower= np.min(np.min(hsv[sides[3,0]:sides[1,0],sides[2,1]:sides[0,1]],axis=1),axis=0)
            lower= np.min(hsvsub,axis=0)
            #upper = np.max(np.max(hsv[sides[3,0]:sides[1,0],sides[2,1]:sides[0,1]],axis=1),axis=0)
            upper = np.max(hsvsub,axis=0)
            thresh = cv2.inRange(hsv,lower,upper)
            contours,hierarchy = cv2.findContours(thresh,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
            #pickle contours to deal with a bug in opencv 2.4.3
            tmp = pickle.dumps(contours)
            contours = pickle.loads(tmp)
            cv2.drawContours(vis,contours,-1,(255,255,255),-1)
            print "got contours"
            flag_click = False
        
        cv2.imshow('edge', vis)
        ch = cv2.waitKey(5)
        if ch == 27:
            break
    cv2.destroyAllWindows()

