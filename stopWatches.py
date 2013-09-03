import time, cv2

def main():
    t0 = time.clock()
    counter = 0
    flagOn = False
    while True:
        keyRet=cv2.waitKey(5)

        if (keyRet=='1'):
            flagOn = not flagOn
            t0 = time.clock()
        elif (keyRet==27):
            break
        
        if flagOn:
            counter = time.clock()-t0
        #print counter

if __name__=="main":
    main()
