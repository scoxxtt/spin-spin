import numpy as np, scipy.io.wavfile as w, subprocess, sys
sr,a=w.read('src.wav'); a=a.astype(np.float32)/32768
def clip(t0,t1,rms=None,fin=0.012,fout=0.04):
    x=a[int(t0*sr):int(t1*sr)].copy(); n1=int(fin*sr); n2=int(fout*sr); x[:n1]*=np.linspace(0,1,n1); x[-n2:]*=np.linspace(1,0,n2); return x
PRE=0.04
words=[clip(0.70-PRE,1.08),clip(1.95-PRE,2.42),clip(3.07-PRE,3.55),clip(4.26-PRE,5.66,fout=0.06)]
# level each word: same loudness (the long first "spin" was much quieter)
def lvl(x,target=0.2):
    r=np.sqrt((x**2).mean())+1e-9; x=x*target/r; return x
words=[lvl(x) for x in words]
# inside the spin block lift the first, quieter "spin" up to the second one
sb=words[3]; cut=int((5.24-(4.26-PRE))*sr); r1=np.sqrt((sb[:cut]**2).mean()); r2=np.sqrt((sb[cut:]**2).mean()); g=np.ones(len(sb)); g[:cut]=min(2.2,r2/r1*0.9); k=int(0.03*sr); g[cut-k:cut]=np.linspace(g[0],1,k); words[3]=lvl(sb*g)
onsets=[0.0,0.50,1.0,1.50]
L=int((onsets[-1]+len(words[3])/sr+0.05)*sr); y=np.zeros(L,np.float32)
for o,x in zip(onsets,words): i=int(o*sr); y[i:i+len(x)]+=x
y/=abs(y).max()/0.9
w.write('dry.wav',sr,(y*32767).astype(np.int16))
TEMPO=1.12
def ring(x,f,mix):
    t=np.arange(len(x))/sr; return x*(1-mix)+x*np.sin(2*np.pi*f*t)*mix*1.6
def make(name,pitch,rf,rmix,chain):
    x=ring(y,rf,rmix); x/=abs(x).max()/0.9; w.write('tmp.wav',sr,(x*32767).astype(np.int16))
    af=f"atempo={TEMPO},asetrate={sr}*{pitch},aresample={sr},atempo={1/pitch:.5f},"+chain+",apad=pad_dur=0.45"
    subprocess.run(['ffmpeg','-v','error','-y','-i','tmp.wav','-af',af,name+'.wav'],check=True)
    s2,z=w.read(name+'.wav'); z=z.astype(np.float32)/32768
    n=int(0.25*s2); z[-n:]*=np.linspace(1,0,n)**2; z/=abs(z).max()/0.92
    w.write(name+'.wav',s2,(z*32767).astype(np.int16))
    subprocess.run(['ffmpeg','-v','error','-y','-i',name+'.wav','-ac','1','-ar','32000','-c:a','libmp3lame','-b:a','56k',name+'.mp3'],check=True)
    print(name,'dur %.2f'%(len(z)/s2))
drive=lambda k:f"volume={k},alimiter=limit=0.95:level=disabled,asoftclip=type=tanh"
make('vo_A',0.93,70,0.22,"highpass=f=110,aecho=1:0.8:7|11:0.42|0.28,"+drive(2.4)+",equalizer=f=3000:t=q:w=1:g=4,acompressor=threshold=0.15:ratio=5:attack=4:release=90:makeup=2,aecho=0.9:0.75:110|220:0.2|0.1")
make('vo_B',0.85,48,0.5,"highpass=f=90,aecho=1:0.8:6|9|14:0.55|0.4|0.3,acrusher=bits=7:mode=log:samples=5:mix=0.35,"+drive(3.2)+",equalizer=f=2500:t=q:w=1:g=5,acompressor=threshold=0.12:ratio=6:attack=3:release=80:makeup=2,aecho=0.9:0.75:120|240:0.2|0.1")
make('vo_C',1.0,90,0.1,"highpass=f=350,lowpass=f=3800,aecho=1:0.8:9:0.25,"+drive(4.5)+",equalizer=f=1800:t=q:w=1:g=5,acompressor=threshold=0.12:ratio=6:attack=3:release=80:makeup=2,aecho=0.9:0.8:130|260|390:0.3|0.18|0.09")
