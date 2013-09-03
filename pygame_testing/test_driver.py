import sys, message_objects as m_o, test, time
from multiprocessing import Process, Pipe, Lock

if __name__ == "__main__":
    parent_conn,child_conn = Pipe()
    lock = Lock()

    mp = Process(target=test.run, args=(child_conn,lock))
    print 'created process'

    mp.start()
    print 'started process'

    #flag is True if the game process is killed
    flag_killed = False
    #time_last is the last time we read from sensors.csv
    

    #storage variables
    theta = 0
    alt = 100
    flag_incr = True

    fid = open('sensors.csv','r')
    #skip the first line, which is labels
    line = fid.readline()
    line = ''
    data = []
    alt = 0
    
    time_last = -10000
    
    while True:
        #update at close to 10 Hz
        if (time.clock()-time_last)>0.1:
            time_last = time.clock()
            line = fid.readline()
            #loop if the EOF is reached
            if len(line)==0:
                fid.close()
                fid = open('sensors.csv','r')
                #skip the first line, which is labels
                line = fid.readline()
                line = fid.readline()
            data = line.rsplit(',')
            data = data[0:9]
            print time_last
            for i in range(len(data)):
                data[i] = float(data[i])
            if data[8]<=600:
                alt = data[8]*0.01
            else:
                alt = data[4]*0.01
        while parent_conn.poll(0.05):
            msg = parent_conn.recv()
            if msg == '**.u.**':#update command received
                lock.acquire()
                parent_conn.send(['ahrs',data[7]*0.01,data[6]*0.01,data[5]*0.01])
                parent_conn.send(['alt',alt])
                parent_conn.send(['gps',data[1],data[2]])
                lock.release()
            elif msg == '**.k.**':#notification that the external process is killing itself
                #lock.acquire()
                print 'external process terminating'
                flag_killed = True
        if flag_killed:
            break

    mp.join()
