import numpy
import sys
import matplotlib.pyplot as plt 
import argparse
import os
import time

class Plot :
    def __init__(self) :
        self.fig, self.ax = plt.subplots()
        self.cid = self.fig.canvas.mpl_connect('button_release_event', self.on_release)
        self.xLimits = None
        backend_toolbar = self.fig.canvas.manager.toolbar
        if backend_toolbar is not None:
            backend_toolbar.zoom()  # Activates the zoom tool automatically

    def on_release(self,event) :
        self.xLimits = plt.xlim()
        print(self.xLimits)
    def xlim(self) :
        return self.xLimits
    def plot(self, x, y) :
        self.ax.plot(x, y)
    def scatter(self,x,y,c) :
        self.ax.scatter(x,y,c=c,cmap='Greys',s=9)
    def set_xlabel(self, label) :
        self.ax.set_xlabel(label)
    def set_ylabel(self, label) :
        self.ax.set_ylabel(label)
    def text(self,x,y,str) :
        self.ax.text(x,y,str,ha='center')
    def show(self) :
        self.xLimits = plt.xlim()
        plt.show()

p = argparse.ArgumentParser()
p.add_argument('--iq',required=True)
p.add_argument('--f-sample',type=float,required=True)
p.add_argument('--amp',help='left,right bounds to skip amplitude graph')
p.add_argument('--modulation',help='left,right bounds to skip modulation graph')
p.add_argument('--preamble',help='left,right bounds to skip preamble graph')
p.add_argument('--fft',action='store_true')
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

amp = numpy.abs(samples)
dangle = numpy.angle(samples[args.N:]*numpy.conj(samples[:-args.N]))/args.N
seconds = numpy.linspace(0,len(dangle)/args.f_sample,len(dangle))
kHz = dangle * args.f_sample / 2e3 / numpy.pi

if None == args.modulation :
    if None == args.amp :
        ms = numpy.linspace(0,1e6*len(amp)/args.f_sample,len(amp))
        p = Plot()
        p.plot(ms,amp)
        p.set_xlabel('Time (ms)')
        p.set_ylabel('Amplitude')
        p.show()
        L,R = p.xlim()
        L = (ms < L).sum()
        R = (ms <= R).sum()
        print('--amp=%d,%d'%(L,R))
    else :
        t = args.amp.split(',')
        L = int(t[0])
        R = int(t[1])
    ms = numpy.linspace(0,1e3*len(kHz)/args.f_sample,len(kHz))
    camp = numpy.zeros((R-L))
    for i in range(args.N) :
        j = i - (args.N >> 1)
        camp += amp[L+j:R+j]
    camp /= args.N
    p = Plot()
    p.scatter(ms[L:R],kHz[L:R],camp)
    p.set_xlabel('Time (ms)')
    p.set_ylabel('Modulation (kHz)')
    p.show()
    L,R = p.xlim()
    L = (ms < L).sum()
    R = (ms <= R).sum()
    print('--modulation=%d,%d'%(L,R))
else :
    t = args.modulation.split(',')
    L = int(t[0])
    R = int(t[1])

    
if args.fft :
    bits = int(numpy.floor(numpy.log2(R-L)))
    fftlength = 1 << bits
    L = (L+R - fftlength) >> 1
    R = L + fftlength
    frequency = numpy.linspace(-args.f_sample/2, args.f_sample/2, fftlength+1, endpoint=True)
    print(frequency[0],frequency[-1])
    fft = numpy.fft.fft(samples[L:R])
    spectrum = numpy.abs(numpy.concat((fft[(fftlength>>1):],fft[0:(fftlength>>1)+1])))
    p = Plot()
    p.plot(frequency/1000, spectrum)
    p.set_xlabel('Frequency (kHz)')
    p.set_ylabel('Amplitude')
    p.show()
    df = (frequency[1:]-frequency[:-1]).mean()
    A = spectrum.sum()*df
    mean = (spectrum*frequency).sum()/spectrum.sum()
    print('A: %f\nmean: %f'%(A,mean))
    quit()
    
if None == args.preamble :
    camp = numpy.zeros((R-L))
    for i in range(args.N) :
        j = i - (args.N >> 1)
        camp += amp[L+j:R+j]
    camp /= args.N
    us = seconds*1e6
    p = Plot()
    p.scatter(us[L:R]-us[L], kHz[L:R], camp)
    p.set_xlabel('time (us)')
    p.set_ylabel('frequency deviation (kHz)')
    p.show()
    Lp,Rp = p.xlim()
    print('L,us[L],Lp,Rp',L,us[L],Lp,Rp)
    Lp = (us < (us[L] + Lp)).nonzero()[0][-1]
    Rp = (us <= (us[L] + Rp)).nonzero()[0][-1]
    mid = (Lp+Rp)>>1
    Lp = int(mid - 4e-6*args.f_sample)
    print('auto:\n--preamble=%d'%(Lp))
else :
    Lp = int(args.preamble)
Rp = int(Lp + 8e-6*args.f_sample)
print('Lp,Rp,Rp-Lp',Lp,Rp,Rp-Lp)
preamble = kHz[Lp:Rp]
offset = preamble.mean()
sine = numpy.sin(2*numpy.pi*seconds[Lp:Rp]*500e3)
cosine = numpy.cos(2*numpy.pi*seconds[Lp:Rp]*500e3)
#plt.plot(seconds[Lp:Rp],100*sine+offset)
#plt.plot(seconds[Lp:Rp],100*cosine+offset)
#plt.scatter(seconds[Lp:Rp],preamble,s=3)
#plt.show()
c_sine = (sine*preamble).mean()
c_cosine = (cosine*preamble).mean()
components = c_sine - 1.j*c_cosine
phase = numpy.angle(components)
depth = 2*numpy.abs(components)
#plt.plot(seconds[Lp:Rp],100*numpy.sin(2*numpy.pi*seconds[Lp:Rp]*500e3-phase))
#plt.show()
print('phase,offset,depth',phase,offset,depth)
print('L,R,R-L,L/20',L,R,R-L,L/20)
L = int(20*numpy.round(Lp/20))
L -= int(numpy.round(20*phase/2/numpy.pi))
symbols = (R - L) // 20
print('L,symbols',L,symbols)
folded = kHz[L:L+20*symbols].reshape((symbols,20))-offset
bits = folded.mean(axis=1)>0

#quit()
camp = numpy.zeros((R-L))
for i in range(args.N) :
    j = i - (args.N >> 1)
    camp += amp[L+j:R+j]
camp /= args.N
p = Plot()
p.scatter(seconds[L:R]*1e6, kHz[L:R], camp)
octet = 0
for i in range(len(bits)) :
    t = L/args.f_sample*1e6 + i + .5
    weight = 1 << (i % 8)
    if bits[i] :
        octet += weight
    #print('%f %d'%(t,bits[i]))
    p.text(t,offset,'%d'%(bits[i]))
    if 128 == weight :
        p.text(t - 4,(offset + 2*depth),'%02x'%(octet))
        octet = 0
p.set_xlabel('time (us)')
p.set_ylabel('frequency deviation (kHz)')
p.show()
quit()

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
    kHz = dangle * args.f_sample / 2e3 / numpy.pi
    fig, ax = plt.subplots()
    cid = fig.canvas.mpl_connect('button_release_event', on_release)
    ax.plot(ms,kHz)
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
    
