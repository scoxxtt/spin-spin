# "hacker with a voice changer" version of the countdown. Needs dry.wav from voice_count.py (words already tightened, before the 12% speed-up)
import numpy as np, scipy.io.wavfile as w, subprocess
sr,y=w.read('dry.wav'); y=y.astype(np.float32)/32768
TEMPO=1.12; rng=np.random.default_rng(7)
ON=[0.036,0.482,0.929,1.375,2.286]   # word starts after the speed-up: three, two, one, spin, spin
def ff(inp,out,af): subprocess.run(['ffmpeg','-v','error','-y','-i',inp,'-af',af,out],check=True)
def rd(p): s,a=w.read(p); return a.astype(np.float32)/32768
def wr(p,a): w.write(p,sr,(np.clip(a,-1,1)*32767).astype(np.int16))
t=np.arange(len(y))/sr
wr('t_in.wav',y*(0.45+0.9*np.sin(2*np.pi*46*t)))                                   # heavy ring modulation = the robot buzz
pit=lambda r:f"atempo={TEMPO},asetrate={sr}*{r},aresample={sr},atempo={1/r:.5f}"
ff('t_in.wav','t_hi.wav',pit(0.82)+",highpass=f=100"); ff('t_in.wav','t_lo.wav',pit(0.60)+",highpass=f=70")   # voice changer: main voice + a deep double under it
a=rd('t_hi.wav'); b=rd('t_lo.wav'); n=min(len(a),len(b)); x=a[:n]+0.5*b[:n]; x/=abs(x).max()
env=np.sqrt(np.convolve(x**2,np.ones(int(sr*0.02))/int(sr*0.02),'same'))
# stutter: the first 45 ms of a word plays twice (written over what follows, so timing does not move)
for T in (ON[0],ON[4]):
    i=int(T*sr); k=int(0.045*sr); x[i+k:i+2*k]=x[i:i+k]
# sample-and-hold bursts: short stretches drop to a very low sample rate
voiced=np.where(env>0.08)[0]
for _ in range(7):
    i=int(rng.choice(voiced)); k=int(rng.uniform(0.04,0.09)*sr); f=int(rng.integers(8,18)); seg=x[i:i+k]; seg[:]=np.repeat(seg[::f],f)[:len(seg)]
# dropouts: the signal cuts out for an instant
for _ in range(4):
    i=int(rng.choice(voiced)); k=int(rng.uniform(0.012,0.022)*sr); x[i:i+k]*=0.05
# electronic noise: hiss that follows the voice, a thin constant static, and data blips in the gaps between words
x=x+rng.standard_normal(n).astype(np.float32)*(env*0.22+0.012)
for T in (ON[0]+0.30,ON[1]+0.33,ON[2]+0.34,ON[4]+0.42):
    for j in range(int(rng.integers(2,4))):
        i=int((T+j*0.035)*sr); k=int(0.022*sr); fq=rng.choice([1200,1800,2400,3200,4200])
        if i+k<n: x[i:i+k]+=0.16*np.sign(np.sin(2*np.pi*fq*np.arange(k)/sr))*np.linspace(1,0.4,k)
x/=abs(x).max()/0.9; wr('t_mix.wav',x)
ff('t_mix.wav','vo_H.wav',"aecho=1:0.8:5|8|13:0.5|0.38|0.28,acrusher=bits=6:mode=log:samples=6:mix=0.5,volume=3.2,alimiter=limit=0.95:level=disabled,asoftclip=type=tanh,equalizer=f=2600:t=q:w=1:g=5,highpass=f=120,acompressor=threshold=0.12:ratio=6:attack=3:release=80:makeup=2,aecho=0.9:0.7:95|190:0.16|0.07,apad=pad_dur=0.4")
z=rd('vo_H.wav'); k=int(0.25*sr); z[-k:]*=np.linspace(1,0,k)**2; z/=abs(z).max()/0.92; wr('vo_H.wav',z)
subprocess.run(['ffmpeg','-v','error','-y','-i','vo_H.wav','-ac','1','-ar','32000','-c:a','libmp3lame','-b:a','56k','vo_H.mp3'],check=True)
print('dur %.2f rms %.3f'%(len(z)/sr,float(np.sqrt((z**2).mean()))))
