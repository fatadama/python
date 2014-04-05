import numpy as np
import bisect

def binary_search(a,x,lo = 0, hi = None):
    hi = hi if hi is not None else a.shape[0]
    #argument a MUST be a 1D numpy array IN DESCENDING ORDER!!
    pos = bisect.bisect_left(a,x,lo,hi)
    pos2 = bisect.bisect_right(a,x,lo,hi)
    return ([pos,pos2] if (pos != hi and a[pos]==x and pos2!=hi and a[pos2-1]==x) else [-1,-1])

def qFind(table,vals):
    #given a loaded Q-matrix "table" of size [M x 4], find the row with the first three
    # entries equal to entries in "vals"
    ind = binary_search(table[:,0],vals[0])
    if not ind[0]==-1:
        ind = binary_search(table[:,1],vals[1],ind[0],ind[1]-1)
        if not ind[0]==-1:
            ind = binary_search(table[:,2],vals[2],ind[0],ind[1]-1)
        else:
            return -10
    else:
        return -10
    return table[ind[0],3]

def load_Q():
    fid = open('Q_stationary.txt','r+')
    count=0
    table = np.zeros([25000, 4],dtype=int)
    for line in fid:
        if not (line[0]=='{') and not (line[0]=='}'):
            #read line
            vals = line.rsplit(',')
            #remove newline character from vals[3]
            vals[3] = vals[3][:-1]#selects all but the last character
            #convert to integers
            for i in range(4):
                vals[i] = int(vals[i])
            table[count,:] = np.array(vals)
            count = count+1
    return table
