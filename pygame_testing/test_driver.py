import sys, message_objects as m_o, test
from multiprocessing import Process, Pipe, Lock

if __name__ == "__main__":
    parent_conn,child_conn = Pipe()
    lock = Lock()

    mp = Process(target=test.run, args=(child_conn,lock))
    print 'created process'

    mp.start()
    print 'started process'

    flag_killed = False

    theta = 0
    alt = 100
    flag_incr = True
    
    while True:
        while parent_conn.poll(0.1):
            msg = parent_conn.recv()
            if msg == '**.u.**':#update command received
                if flag_incr:
                    theta = theta + 1
                else:
                    theta = theta-1
                if abs(theta)>15:
                    flag_incr = not flag_incr
                lock.acquire()
                parent_conn.send(['ahrs',10,theta,3])
                parent_conn.send(['alt',alt])
                lock.release()
            elif msg == '**.k.**':#notification that the external process is killing itself
                #lock.acquire()
                print 'external process terminating'
                flag_killed = True
        if flag_killed:
            break

    mp.join()
