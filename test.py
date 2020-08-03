import csv,sys,io
import subprocess as proc
from functools import partial

def menuload(filename):
    menucontent = []
    with open('menu.csv') as csvfile:
        r = csv.reader( csvfile )
        first = True
        for row in r:
            if first: 
                first = False
                continue
            if row[0][0] == '#':
                continue    
            row[0] = row[0].replace(u'|',u'\n')
            menucontent.append( row )
    return menucontent if len(menucontent)>0 else False    

def myexec( label='', menu=False, arg=False ):
    if arg==False:
        return
    a = []
    for item in arg.split(' '):
        if item != '':
            a.append(item)    
    r = str(proc.check_output( a ), encoding='utf-8').strip()
    #print( r )    
    return r        
       
m = menuload( 'menu.csv' )

f=[]        
for ex in m: 
    if ex[1] == 'f':
        f.append( [ ex[0], partial(myexec,arg=ex[2]) ] )
        
for mx in f:        
    print( 'Label:\n',mx[0], '\nResult:\n', mx[1]( label=mx[0], menu=False ), '\n--------' )        