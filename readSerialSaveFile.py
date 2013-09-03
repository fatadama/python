import datetime
import os.path
import time
import msvcrt
import serial

def keyboardTimeOut(timeout = 50):
    now = time.time()
    inp = ''
    chr = '\0'
    while True:
        if msvcrt.kbhit():
            chr = msvcrt.getche()
        if ord(chr) >= 32: #space_char
            inp += chr
            chr = '\0'
        if (time.time()-now)>(0.001*timeout):
            break
    return inp

#write file format: 'date_##.txt'. ## begins at 1, increases for each existing log
today = datetime.date.today()
filenum = 1
filename = 'serialLogs/' + today.__str__() + '_' + str(filenum) +'.txt'

#check for file existance, repeat until new file created
while os.path.isfile(filename):
    filenum = filenum+1
    filename = 'serialLogs/' + today.__str__() + '_' + str(filenum) +'.txt'

print "Opening log file", filename

#open file
f = open(filename,'w')

timeout = 50

ser = serial.Serial()
ser.baudrate=115200
ser.port = 'COM5'
ser.timeout = timeout

print "Attemping to connect to port", ser.port, "at ", ser.baudrate, " baud"

ser.open()

if ser.isOpen():
    print "Serial port open"
    #read from serial
    while(True):
        #read serial
        line = ser.readline()
        #print serial line:
        print line
        f.write(line)
        f.write('\n')
        #read user input:
        inp = keyboardTimeOut(timeout)
        if len(inp)>0:
            ser.write(inp)
            #print inp
else:
    print 'Unable to open serial port'

#these will never be reached
f.close()
ser.close()
