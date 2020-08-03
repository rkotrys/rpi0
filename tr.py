import numpy as np

def dat(v):
    y = []
    for x in v:
        y.append( [x[0],x[1],1] )
    return np.array(y,np.float32).T

# translacja, 
# x - lista punktów [(x,y),...] 
# p - przesunięcie (dx,dy)
def tr(x,p):      
    t = np.float32(np.eye(3))
    t[0,2] = p[0]
    t[1,2] = p[1]
    y = t @ x
    return y[:2].T.tolist() 
    
def l2t(l):
    y = []
    for n in l:
        y.append( (n[0],n[1]) )
    return y               

