import numpy
import sys
import matplotlib.pyplot as plt 
import argparse
import os
import time

p = argparse.ArgumentParser()
p.add_argument('--iq',required=True)
p.add_argument('--amp',action='store_true')
p.add_argument('--sine',action='store_true')
p.add_argument('--left')
p.add_argument('--right')
p.add_argument('--N',type=int,default=1)

args = p.parse_args()

if len(sys.argv) < 2 :
    print('Usage: %s <raw-data>'%(sys.argv[0]))
    quit()
    
raw = numpy.frombuffer(open(args.iq,'rb').read(),dtype=numpy.int8)
length = len(raw)
if length & 1 :
    raise RuntimeError('length is odd (%d)'%(length))

folded = raw.reshape((length>>1,2))
samples = folded[:,0] + 1.0j*folded[:,1]

dangle = numpy.angle(samples[args.N:]*numpy.conj(samples[:-args.N]))

print(dangle[:10])
print(dangle.min(),dangle.max(),dangle.mean(),dangle.std())

amp = numpy.abs(samples)
print(amp.min(),amp.max())

count,edges = numpy.histogram(amp,100)

fh = open('histo.data','w')
for i in range(100) :
    l = edges[i]
    r = edges[i+1]
    fh.write('%d 0\n%d %f\n%d %f\n%d 0\n'%(l,l,count[i],r,count[i],r))
fh.close()

us = numpy.linspace(0,len(dangle)/20,len(dangle))
prev = 0

if(args.amp) :
    fh = open('amp.data','w')
    high = False
    for i in range(len(amp)) :
        t = amp[i] > 40
        if t == high : continue
        if prev > 0 :
            print('%f us at %d(%d)'%(us[i]-prev,high, i))
        prev = us[i]
        fh.write('%d %d\n%d %d\n'%(i,high,i,t))
        high = t
    fh.close()
    ph = os.popen('gnuplot','w')
    ph.write('plot "amp.data" w l\n')
    ph.flush()
    time.sleep(60)
    quit()
    
if(0) :
    fh = open('dphase.data','w')
    for i in range(1170,9130) :
        fh.write('%f %f\n'%((i-131040)/8,dangle[i]))
    fh.close()
    
if(1) :
    L = int(args.left)
    R = int(args.right)
    fig,main = plt.subplots()
    main.scatter(us[L:R], dangle[L:R]/2/numpy.pi*20e3/args.N, c = amp[L:R] , cmap = "Greys")
    main.set_xlabel('time (us)')
    main.set_ylabel('frequency deviation (kHz)')
    if args.sine :
        main.plot(us[L:R], numpy.cos(us[L:R]*2*numpy.pi/2)*300-150)
    plt.show()
    
