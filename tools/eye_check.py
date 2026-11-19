# 檢查 BOSS 頭像的瞳孔座標：python3 tools/eye_check.py '{"rex":[[117.5,110.5],[165.4,111]]}' out.png ，每個眼睛放大 7 倍並畫紅色準星與 ±px 刻度，準星要落在瞳孔正中央才填進 defBoss 的 eyes
import sys, json
from PIL import Image, ImageDraw
E=json.loads(sys.argv[1]); out=sys.argv[2]
Z=7; R=16; tiles=[]
for n,es in E.items():
  im=Image.open(f'/home/claude/spin-spin/art/portraits/{n}.jpg').convert('RGB')
  for i,(x,y) in enumerate(es):
    c=im.crop((int(x)-R,int(y)-R,int(x)+R,int(y)+R)).resize((2*R*Z,2*R*Z),Image.LANCZOS); d=ImageDraw.Draw(c)
    ox,oy=(x-int(x)+R)*Z,(y-int(y)+R)*Z
    d.ellipse([ox-4,oy-4,ox+4,oy+4],outline=(255,0,0),width=2); d.line([(ox-18,oy),(ox-7,oy)],fill=(255,0,0),width=2); d.line([(ox+7,oy),(ox+18,oy)],fill=(255,0,0),width=2); d.line([(ox,oy-18),(ox,oy-7)],fill=(255,0,0),width=2); d.line([(ox,oy+7),(ox,oy+18)],fill=(255,0,0),width=2)
    for k in range(-12,13,4): d.text((ox+k*Z-4,2),f'{k:+d}',fill=(0,255,255)); d.text((2,oy+k*Z-5),f'{k:+d}',fill=(255,0,255))
    d.text((4,2*R*Z-12),f'{n}{i} ({x},{y})',fill=(255,255,0)); tiles.append(c)
W=2*R*Z; cols=4; rows=(len(tiles)+cols-1)//cols; c=Image.new('RGB',(W*cols,W*rows))
for i,t in enumerate(tiles): c.paste(t,((i%cols)*W,(i//cols)*W))
c.save(out)
