"""Anlatım parçalarını birleştirir: zaman çizelgesi (timeline.json) + ses (ses.wav)."""
import json, sys, subprocess, numpy as np, re
sys.path.insert(0,'/home/claude/kuranikerim_tr')
import os; os.environ['KT_VOICE']='mcp'
import voice as VO, music as MU, render as R
SR=VO.SR
segs=json.load(open('segs.json'))
REF={3:'60. ayet',5:'62-63. ayetler',6:'64. ayet',7:'65. ayet',8:'66-68. ayetler',9:'69-70. ayetler',11:'71-73. ayetler',13:'74. ayet',14:'74-75. ayetler',15:'76. ayet',
     16:'77. ayet',17:'77. ayet',18:'78. ayet',20:'79. ayet',22:'80-81. ayetler',24:'82. ayet',26:'82. ayet',27:'68. ayet'}
def trim(a):
    hop=int(.01*SR); n=len(a)//hop
    rms=np.sqrt(np.mean(a[:n*hop].reshape(n,hop)**2,axis=1)+1e-12)
    on=np.where(rms>max(.004,np.percentile(rms,95)*.04))[0]
    a=a[max(0,on[0]-4)*hop:min(len(a),(on[-1]+14)*hop)].copy()
    f=int(.03*SR); a[:f]*=np.linspace(0,1,f); a[-f:]*=np.linspace(1,0,f); return a
def pauses(a):
    hop=int(.01*SR); n=len(a)//hop
    rms=np.sqrt(np.mean(a[:n*hop].reshape(n,hop)**2,axis=1)+1e-12)
    q=rms<max(.006,np.percentile(rms,90)*.07); out=[]; i=0
    while i<n:
        if q[i]:
            j=i
            while j<n and q[j]: j+=1
            if (j-i)*.01>=.18 and i>5 and j<n-5: out.append(((i+j)/2*.01,(j-i)*.01))
            i=j
        else: i+=1
    return out
def sentences(text):
    """Cümlelere böl; her kelimeye tırnak içinde mi bayrağı."""
    words=[]; inq=False
    for w in text.split():
        st=inq or w.startswith('"')
        if w.count('"')%2==1: inq=not inq
        words.append((w.replace('"',''),st))
    sents=[[]]
    for w,qf in words:
        sents[-1].append((w,qf))
        if w[-1] in '.!?' : sents.append([])
    return [s for s in sents if s]
def wt(w): return len(w)+(7 if w[-1] in '.!?' else 4 if w[-1] in ',;:' else 1)
def chunks(sent, maxc=46):
    out=[[]]
    for w,qf in sent:
        cur=out[-1]
        if cur and (sum(len(x[0])+1 for x in cur)+len(w)>maxc or cur[-1][1]!=qf or (cur[-1][0][-1] in ';:' and len(cur)>=3)): out.append([])
        out[-1].append((w,qf))
    # tek kelimelik yetimleri birleştir
    i=1
    while i<len(out):
        if len(out[i])==1 and out[i][0][1]==out[i-1][-1][1] and sum(len(x[0])+1 for x in out[i-1])+len(out[i][0][0])<maxc+10:
            out[i-1]+=out.pop(i)
        else: i+=1
    return out
GAP, CHGAP, LEAD = 0.5, 2.0, 0.25
audio=[np.zeros(int(LEAD*SR),np.float32)]; t=LEAD; TL=[]; CH=[]
for i,s in enumerate(segs):
    a=R.level(trim(VO._decode(f'vo/{i:02d}.mp3'))); d=len(a)/SR
    if not CH or CH[-1]['ad']!=s['bolum']:
        if CH:
            audio.append(np.zeros(int((CHGAP-GAP)*SR),np.float32)); t+=CHGAP-GAP
        CH.append(dict(ad=s['bolum'],sahne=s['sahne'],start=t))
    sents=sentences(s['text']); W=[sum(wt(w) for w,_ in se) for se in sents]; tot=sum(W)
    ps=pauses(a); bounds=[0.0]; acc=0
    for k in range(len(sents)-1):
        acc+=W[k]; exp=d*acc/tot
        cand=[p for p in ps if abs(p[0]-exp)<1.6 and p[0]>bounds[-1]+.4]
        bounds.append(max(cand,key=lambda p:p[1]-abs(p[0]-exp)*.25)[0] if cand else max(exp,bounds[-1]+.4))
    bounds.append(d); caps=[]
    for k,se in enumerate(sents):
        b0,b1=bounds[k],bounds[k+1]; cs=chunks(se); cw=[sum(wt(w) for w,_ in c) for c in cs]; x=b0
        for c,w in zip(cs,cw):
            dd=(b1-b0)*w/sum(cw); caps.append(dict(text=' '.join(z[0] for z in c),q=c[0][1],start=t+x,end=t+x+dd)); x+=dd
    TL.append(dict(i=i,bolum=s['bolum'],start=t,end=t+d,caps=caps,ref=REF.get(i)))
    audio+= [a,np.zeros(int(GAP*SR),np.float32)]; t+=d+GAP
t+=2.5; audio.append(np.zeros(int(2.5*SR),np.float32))
for k,c in enumerate(CH): c['end']=CH[k+1]['start'] if k+1<len(CH) else t
json.dump(dict(total=t,segs=TL,ch=CH),open('timeline.json','w'),ensure_ascii=False,indent=1)
R.write_wav('raw.wav',np.concatenate(audio),SR); VO.master('raw.wav','vo.wav')
R.MUSIC_VOL=0.16
MU.make(t+1,4242,'mu.wav',style='ilahi'); R.mix_audio('vo.wav','mu.wav','ses.wav')
print('toplam',round(t,1),'sn', len(TL),'parça')
for c in CH: print(f"{int(c['start']//60)}:{int(c['start']%60):02d} {c['ad']}")
