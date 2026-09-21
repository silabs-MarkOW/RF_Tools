import numpy
import sys
import matplotlib.pyplot as plt 
import argparse
import os
import time

p = argparse.ArgumentParser()
p.add_argument('--iq',required=True)
p.add_argument('--f-sample',type=float,required=True)
p.add_argument('--amp',action='store_true')
p.add_argument('--sine',action='store_true')
p.add_argument('--left')
p.add_argument('--right')
p.add_argument('--preamble')
p.add_argument('--N',type=int,default=1)

args = p.parse_args()

if len(sys.argv) < 2 :
    print('Usage: %s <raw-data>'%(sys.argv[0]))
    quit()
    
raw = numpy.frombuffer(open(args.iq,'rb').read(),dtype=numpy.int8)
length = len(raw)
if length & 1 :
    raise RuntimeError('length is odd (%d)'%(length))

length >>= 1
folded = raw.reshape((length,2))
p2length = 1 << int(numpy.floor(numpy.log2(length)))

samples = folded[:,0] + 1.0j*folded[:,1]
print('%d samples (%f -> %d)'%(length,numpy.log2(length),p2length))

dangle = numpy.angle(samples[args.N:]*numpy.conj(samples[:-args.N]))

print(dangle[:10])
print(dangle.min(),dangle.max(),dangle.mean(),dangle.std())

amp = numpy.abs(samples)
print('Amplitude: %.1f - %.1f'%(amp.min(),amp.max()))

count,edges = numpy.histogram(amp,100)

fh = open('histo.data','w')
for i in range(100) :
    l = edges[i]
    r = edges[i+1]
    fh.write('%d 0\n%d %f\n%d %f\n%d 0\n'%(l,l,count[i],r,count[i],r))
fh.close()

us = numpy.linspace(0,len(dangle)/20,len(dangle))
prev = 0

xLimits = None
def on_release(event) :
    global xLimits
    print('limits:',plt.xlim())
    xLimits = plt.xlim()
    
if None == args.left or None == args.right :
    ms = numpy.linspace(0,length/args.f_sample*1e3,length)
    fig, ax = plt.subplots()
    cid = fig.canvas.mpl_connect('button_release_event', on_release)
    ax.plot(ms,amp)
    ax.set_xlabel('time (ms)')
    ax.set_ylabel('Amplitude (8-bit (complex sample)')
    plt.show()
    L = (ms < xLimits[0]).nonzero()[0][-1]
    R = (ms > xLimits[1]).nonzero()[0][0]
    print('auto:\n--left=%d --right=%d'%(L,R))
else :
    L = int(args.left)
    R = int(args.right)

modulation = numpy.angle(samples[L:R+args.N]*numpy.conj(samples[L-args.N:R]))/2/numpy.pi*args.f_sample/args.N
length = len(modulation)
mamp = numpy.zeros((length))
for i in range(args.N) :
    mamp += amp[L-i:R+args.N-i]
mamp /= args.N
us = numpy.linspace(0,length/args.f_sample*1e6,length)
               
if None == args.preamble :
    fig,ax = plt.subplots()
    cid = fig.canvas.mpl_connect('button_release_event', on_release)
    ax.scatter(us, modulation/1e3, c = mamp , cmap = "Greys")
    ax.set_xlabel('time (us)')
    ax.set_ylabel('frequency deviation (kHz)')
    if args.sine :
        ax.plot(us, numpy.cos(us*2*numpy.pi/2)*300-150)
    plt.show()
    L = (us < xLimits[0]).nonzero()[0][-1]
    R = (us > xLimits[1]).nonzero()[0][0]
    mid = (L+R)>>1
    L = int(mid - 4e-6*args.f_sample)
    print('auto:\n--preamble=%d'%(L))
else :
    L = int(args.preamble)
R = int(L + 8e-6*args.f_sample)
preamble = modulation[L:R]
sine = numpy.sin(numpy.pi*us[L:R])
cosine = numpy.cos(numpy.pi*us[L:R])
c_sine = (sine*preamble).mean()
c_cosine = (cosine*preamble).mean()
components = c_sine - 1.j*c_cosine
phase = numpy.angle(components)
offset = preamble.mean()
depth = 2*numpy.abs(components)
print(phase,offset,depth)
print(L,R,R-L,L/20)
L = int(20*numpy.round(L/20))
L -= int(numpy.round(20*phase/2/numpy.pi))
symbols = (length - L) // 20
print(L,symbols)
folded = modulation[L:L+20*symbols].reshape((symbols,20))-offset
bits = folded.mean(axis=1)>0

#quit()
fig,ax = plt.subplots()
ax.scatter(us, modulation/1e3, c = mamp, s=9 , cmap = "Greys")
#ax.plot(us,(offset+depth*numpy.sin(numpy.pi*us-phase))/1e3)
octet = 0
for i in range(len(bits)) :
    t = L/args.f_sample*1e6 + i + .5
    weight = 1 << (i % 8)
    if bits[i] :
        octet += weight
    #print('%f %d'%(t,bits[i]))
    ax.text(t,offset/1e3,'%d'%(bits[i]),ha='center')
    if 128 == weight :
        ax.text(t - 4,(offset + 2*depth)/1e3,'%02x'%(octet))
        octet = 0
ax.set_xlabel('time (us)')
ax.set_ylabel('frequency deviation (kHz)')
plt.show()

quit()
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
    fig,main = plt.subplots()
    main.scatter(us[L:R], dangle[L:R]/2/numpy.pi*20e3/args.N, c = amp[L:R] , cmap = "Greys")
    main.set_xlabel('time (us)')
    main.set_ylabel('frequency deviation (kHz)')
    if args.sine :
        main.plot(us[L:R], numpy.cos(us[L:R]*2*numpy.pi/2)*300-150)
    plt.show()
    
