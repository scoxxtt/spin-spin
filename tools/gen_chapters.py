# Generates all 15 chapters of track levels from segment templates (v0.31: new road mechanics, longer roads).
# usage: python3 tools/gen_chapters.py          -> rewrites the whole CHAPTERS list in js/chapters.js (fixed seed: same output every run)
#        python3 tools/gen_chapters.py --print  -> print only
# Chapters 1-5 keep their hand-made names, BOSSes, goals, stars and rewards (tools/base_1_5.json); every road is regenerated.
import random, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
R = random.Random(731)
def js(o):
    if isinstance(o, dict): return '{ ' + ', '.join(f"{k}: {js(v)}" for k, v in o.items()) + ' }'
    if isinstance(o, list): return '[' + ', '.join(js(v) for v in o) + ']'
    if isinstance(o, str): return "'" + o.replace("'", "\\'") + "'"
    if isinstance(o, bool): return 'true' if o else 'false'
    if isinstance(o, float): return f'{round(o, 2):g}'
    return str(o)
def S(props=None, gaps=None, sign=None, used=300, **ex): return dict(props=props or [], gaps=gaps or [], sign=sign, used=used, ex=ex)
sd = lambda: R.choice([-1, 1])
# ---- segments: each places its pieces from track distance y and returns how much road it used. c = chapter config (c['no'] scales the difficulty) ----
def seg_bumpers(y, c):  return S([dict(type='bumper', x=-0.45, y=y + 60), dict(type='bumper', x=0.45, y=y + 60), dict(type='bumper', x=R.choice([-0.15, 0.15]), y=y + 220)], used=320)
def seg_boost(y, c):    return S([dict(type='boost', x=R.choice([-0.2, 0, 0.2]), y=y + 40)], used=200)
def seg_wind(y, c):
    d = R.choice([3, 9]); side = 0.55 if d == 3 else -0.55
    return S([dict(type='wind', x=0, y=y + 150, l=260, w=380, dir=d, power=0.7), dict(type='spikes', x=side, y=y + 180, r=34, on=2, off=2)], sign=('CROSSWIND', '#e9f2ff'), used=340)
def seg_barrels(y, c):  return S([dict(type='boost', x=0, y=y + 20), dict(type='barrel', x=-0.3, y=y + 200), dict(type='barrel', x=0.3, y=y + 200), dict(type='crack', x=0, y=y + 260, len=380, rot=3, hp=c['crack'])], sign=('EXPLOSIVE', '#ff2a55'), used=380)
def seg_firewall(y, c): return S([dict(type='boost', x=0, y=y + 30), dict(type='crack', x=0, y=y + 250, len=380, rot=3, hp=c['crack'])], sign=('FIREWALL', '#c9ced6'), used=340)
def seg_magnet(y, c):
    sx = R.choice([-0.4, 0.4])
    return S([dict(type='magnet', x=sx, y=y + 160, r=130), dict(type='spikes', x=sx, y=y + 160, r=30), dict(type='magnet', x=-sx, y=y + 330, r=120, power=-1)], sign=('EM FIELD', '#00f0ff'), used=420)
def seg_laser(y, c):
    c['lz'] = -c.get('lz', 0.21); ph = round(R.uniform(0, 1.5), 1)
    return S([dict(type='laser', x=c['lz'], y=y + 120, len=300, on=1.1, off=2.1, phase=ph)], sign=('LASER GRID', '#ff2a55'), used=260)
def seg_spinner(y, c):  return S([dict(type='mover', x=R.choice([-0.25, 0.25]), y=y + 150, len=110, move='spin', speed=R.choice([0.14, -0.14]))], used=300)
def seg_ice(y, c):      return S([dict(type='ice', x=0, y=y + 150, l=260, w=380), dict(type='bumper', x=R.choice([-0.3, 0.3]), y=y + 160)], sign=('ICE', '#a8fbff'), used=330)
def seg_portal(y, c):
    c['pid'] = c.get('pid', 0) + 1; a, b = f"p{c['pid']}a", f"p{c['pid']}b"; sx = R.choice([-0.45, 0.45])
    return S([dict(type='portal', id=a, x=sx, y=y + 80, to=b), dict(type='portal', id=b, x=-sx * 0.6, y=y + 470), dict(type='spikes', x=-sx * 0.5, y=y + 260, r=42, on=2, off=2), dict(type='laser', x=0.21, y=y + 330, len=300, on=1.1, off=2.1)], sign=('WARP', '#ff9ae6'), used=540)
def seg_spikes(y, c):   return S([dict(type='spikes', x=-0.35, y=y + 100, r=42, on=2, off=2, skin=c['skin']), dict(type='spikes', x=0.35, y=y + 240, r=42, on=2, off=2, phase=1, skin=c['skin'])], used=340)
def seg_gap(y, c):
    s = R.choice(['L', 'R']); return S([dict(type='bumper', x=0.3 if s == 'L' else -0.3, y=y + 140)], [dict(side=s, **{'from': y + 60}, to=y + 200)], ('DANGER GAP', '#ff2a55'), 300)
def seg_slide(y, c):    return S([dict(type='mover', x=0, y=y + 140, len=90, rot=12, move='slide', span=70, period=2.6)], used=280)
# ---- v0.31 road mechanics ----
LANES = (-0.62, 0.0, 0.62)   # v0.48.1: optional routes sit in one of three lanes (left / middle / right), each under a third of the road
def lane(y, k=0): return LANES[(y // 100 + k) % 3]          # deterministic (no draw from R), so everything else in a level stays put
def seg_ramp(y, c):     # narrow jump ramp in one lane: fly over the hazard in that lane, or go round it on the open road
    n = c['no']; x = lane(y); over = dict(type='bumper', x=x, y=y + 440) if n < 3 else dict(type='spikes', x=x, y=y + 440, r=44, on=2, off=1.5)
    return S([dict(type='boost', x=x, y=y + 40), dict(type='ramp', x=x, y=y + 230, w=110, l=80), over], sign=('JUMP', '#fcee0a'), used=1000)
def seg_deck(y, c):     # v0.52: 2F side road in four shapes, so the shortcuts are not all alike
    k = lane(y); v = (y // 100) % 4; nb = lane(y, 1)
    if v == 0:   # short hop
        return S([dict(type='boost', x=k, y=y + 30)], sign=('2F', '#7fdfff'), used=700, decks=[dict(x=k, w=120, y=y + 200, l=260, h=1, up=130, down=130)])
    if v == 1:   # long skyway
        return S([dict(type='boost', x=k, y=y + 30)], sign=('SKYWAY', '#7fdfff'), used=1080, decks=[dict(x=k, w=120, y=y + 200, l=640, h=1, up=150, down=150)])
    if v == 2:   # snake: three linked platforms stepping across the lanes (left→middle→right or back)
        seq = [-0.62, 0.0, 0.62] if k <= 0 else [0.62, 0.0, -0.62]
        ds = [dict(x=seq[0], w=120, y=y + 200, l=300, h=1, up=150), dict(x=seq[1], w=120, y=y + 450, l=300, h=1), dict(x=seq[2], w=120, y=y + 700, l=300, h=1, down=150)]
        return S([dict(type='boost', x=seq[0], y=y + 30)], sign=('SNAKE', '#ff9ae6'), used=1220, decks=ds)
    # twin: two lanes of different lengths side by side
    return S([dict(type='boost', x=k, y=y + 30)], sign=('2F', '#7fdfff'), used=900, decks=[dict(x=k, w=120, y=y + 200, l=420, h=1, up=150, down=150), dict(x=nb, w=110, y=y + 330, l=260, h=1, up=130, down=130)])
def seg_deck2(y, c):    # 2F lane with a narrower 3F block on it: drop back to 2F off its end
    k = lane(y)
    return S([dict(type='boost', x=k, y=y + 30)], sign=('3F', '#7fdfff'), used=990, decks=[dict(x=k, w=124, y=y + 190, l=560, h=1, up=150, down=150), dict(x=k, w=96, y=y + 270, l=280, h=2, up=100)])
def seg_deck3(y, c):    # two side-by-side lanes: 2F/3F/4F tower in one, a plain 2F run in another
    k = lane(y); k2 = lane(y, 1)
    return S([dict(type='boost', x=k, y=y + 30)], sign=('4F', '#ff9ae6'), used=1180, decks=[dict(x=k, w=124, y=y + 190, l=760, h=1, up=150, down=150), dict(x=k, w=100, y=y + 260, l=500, h=2, up=100), dict(x=k, w=84, y=y + 360, l=230, h=3, up=90), dict(x=k2, w=110, y=y + 330, l=420, h=1, up=150, down=150)])
def seg_belt(y, c):
    n = c['no']
    if n < 4: return S([dict(type='belt', x=0, y=y + 170, w=200, l=280, dir=12, power=0.8), dict(type='bumper', x=-0.62, y=y + 170), dict(type='bumper', x=0.62, y=y + 170)], sign=('BELT', '#fcee0a'), used=400)
    s = R.choice(['L', 'R']); return S([dict(type='belt', x=0, y=y + 160, w=380, l=220, dir=9 if s == 'L' else 3, power=round(min(0.7, 0.4 + 0.02 * n), 2))], [dict(side=s, **{'from': y + 70}, to=y + 260)], ('BELT', '#fcee0a'), 380)
def seg_tube(y, c):     # wormhole tube: skips a laser + spikes section; from chapter 6 the mouth opens and shuts
    n = c['no']; s = sd() * 0.5; t = dict(type='tube', x=s, y=y + 100, ex=round(-s * 0.3, 2), ey=y + 760, bend=0.2)
    if n >= 6: t.update(open=3.2, ph=round(R.uniform(0, 3), 1))
    return S([t, dict(type='laser', x=0.21 * (1 if s < 0 else -1), y=y + 330, len=300, on=1.1, off=2.1, phase=round(R.uniform(0, 1.5), 1)), dict(type='spikes', x=round(-s * 0.4, 2), y=y + 520, r=42, on=2, off=2)], sign=('TUBE', '#ff4fd8'), used=880)
def seg_rail(y, c):
    s = sd() * 0.5; return S([dict(type='rail', x=s, y=y + 80, x2=s, y2=y + 620), dict(type='spikes', x=round(-s * 0.3, 2), y=y + 260, r=42, on=2, off=2), dict(type='bumper', x=round(-s * 0.5, 2), y=y + 460)], sign=('GRIND', '#fcee0a'), used=720)
def seg_bridge(y, c):   # chasm with planks: wide pair early, one swaying plank from chapter 9
    n = c['no']; L = min(320, 220 + 8 * n)
    if n < 9: w = max(72, 120 - 4 * n); planks = [dict(x=-0.45, w=w), dict(x=0.45, w=w)]
    else: planks = [dict(x=round(sd() * 0.3, 2), w=110, sway=16 + n * 3 // 2, ph=round(R.uniform(0, 3), 1))]
    return S(sign=('CHASM', '#ff2a55'), used=120 + L + 160, chasms=[dict(y=y + 120, l=L, planks=planks)])
def seg_jumpgap(y, c):  # ramp jump over a chasm (a narrow spare plank until chapter 6)
    n = c['no']; L = 180 + min(100, 6 * n); pl = [dict(x=round(sd() * 0.62, 2), w=64)] if n < 6 else []
    return S([dict(type='boost', x=0, y=y + 30), dict(type='ramp', x=0, y=y + 200, w=380, l=80)], sign=('JUMP', '#fcee0a'), used=max(1000, 300 + L + 260), chasms=[dict(y=y + 300, l=L, planks=pl)])
def seg_railgap(y, c):  # a rail runs across the chasm; a thin plank on the other side until chapter 9
    n = c['no']; s = sd() * 0.4; pl = [dict(x=round(-s * 1.2, 2), w=70 if n < 9 else 56)]
    return S([dict(type='rail', x=s, y=y + 60, x2=s, y2=y + 660)], sign=('GRIND', '#fcee0a'), used=780, chasms=[dict(y=y + 240, l=280, planks=pl)])
def seg_turn(y, c):
    n = c['no']; return S([dict(type='turn', x=0, y=y + 200, r=105, speed=round(sd() * (0.35 + 0.02 * n), 2)), dict(type='spikes', x=-0.64, y=y + 200, r=32, on=2, off=2), dict(type='spikes', x=0.64, y=y + 200, r=32, on=2, off=2, phase=1)], sign=('TURNTABLE', '#7fdfff'), used=420)
def seg_switch(y, c):   # locked door across the road: press the switch in the side pocket first (from chapter 9 it only stays open for a few seconds)
    n = c['no']; c['sid'] = c.get('sid', 0) + 1; i = f"s{c['sid']}"; s = sd(); sw = dict(type='switch', x=round(s * 0.62, 2), y=y + 250, id=i)
    if n >= 9: sw['time'] = max(5, 9 - n // 3)
    return S([sw, dict(type='spikes', x=round(-s * 0.2, 2), y=y + 300, r=40, on=2, off=2), dict(type='door', x=0, y=y + 470, len=380, lock=i)], sign=('SWITCH', '#fcee0a'), used=580)
def seg_branch(y, c):   # a wall splits the road: one lane has spikes and bumpers, the other a belt running backwards
    s = sd(); return S([dict(type='wall', x=0, y=y + 300, len=440, rot=12), dict(type='spikes', x=-0.5 * s, y=y + 200, r=36, on=2, off=2), dict(type='bumper', x=-0.5 * s, y=y + 400), dict(type='belt', x=0.5 * s, y=y + 300, w=170, l=300, dir=6, power=0.4)], sign=('BRANCH', '#7fdfff'), used=620)
def seg_crumble(y, c):  # collapsing floor across the road (from chapter 11 behind a one-way gate)
    n = c['no']; p = [dict(type='boost', x=0, y=y + 20)] + ([dict(type='oneway', x=0, y=y + 70)] if n >= 11 else [])
    return S(p, sign=('CRUMBLE', '#ff9f1a'), used=380, crumble=[dict(x=0, y=y + 190, w=380, l=192)])
def seg_lift(y, c):     # a lift across the whole road: drive on while it is down, ride it up, drop off the far end
    return S([dict(type='boost', x=0, y=y + 40)], sign=('LIFT', '#7fdfff'), used=560, decks=[dict(x=0, w=380, y=y + 200, l=220, h=1, b=0, lift=3.6, ph=round(R.uniform(0, 3), 1))])
SEGS = {k[4:]: v for k, v in globals().items() if k.startswith('seg_')}
PN = dict(bumpers='彈力柱', wind='強風', barrels='炸藥桶＋防火牆', firewall='防火牆', magnet='磁鐵', laser='雷射', spinner='旋轉擋板', ice='冰面', portal='傳送門', spikes='地刺', gap='缺口', slide='推板',
          ramp='跳台', deck='高台 2F', deck2='高台 3F', deck3='高台 4F', belt='輸送帶', tube='蟲洞管道', rail='滑軌', bridge='獨木橋', jumpgap='跳台飛越深淵', railgap='滑軌跨越深淵', turn='旋轉圓盤', switch='開關門',
          branch='分岔路', crumble='崩塌地板', lift='升降台', dark='黑暗區', lowg='低重力', chase='病毒牆')
EXPL = dict(ramp='第一次出現跳台：夠快衝上去就會飛起來，越過前面的障礙。', bumpers='彈力柱會把你大力彈開，可以借力轉彎。', deck='第一次出現高台：從斜坡開上 2F，邊緣會掉回下一層，不會死但會頓一下。',
            spikes='地刺一亮一滅，踩在上面轉速會一直掉。', belt='第一次出現輸送帶：會一路把你往箭頭方向送。', spinner='旋轉擋板被掃到會被打飛，等它轉過去再衝。',
            ice='第一次出現冰面：在上面拖曳幾乎沒用，進去前先對好方向。', tube='第一次出現蟲洞管道：鑽進粉紅色洞口，會從管子一路被送到很前面。', bridge='第一次出現深淵：沒有地板的地方只能走獨木橋，掉下去算一條命。',
            portal='第一次出現傳送門：衝進 WARP 門會從 EXIT 門出來。', firewall='第一次出現防火牆：有血條的灰牆，用力撞破才過得去。', gap='第一次出現牆的缺口：缺口那一側沒有牆，衝出去就出界。',
            wind='第一次出現強風：會一直把你往箭頭方向吹。', barrels='第一次出現炸藥桶：一撞就爆還會連鎖，把敵人引過去再撞。', jumpgap='跳台可以直接飛過深淵：速度不夠會掉下去，先踩加速帶。', turn='第一次出現旋轉圓盤：會帶著你繞圈再甩出去。',
            magnet='第一次出現磁鐵：紅圈吸、青圈推。', laser='第一次出現雷射柵欄：亮的時候撞到會被彈回扣血。', rail='第一次出現滑軌：順著方向擦上黃色軌道就會自動高速滑行，往旁邊拖曳可以跳下來。', railgap='滑軌也能直接滑過深淵。',
            switch='第一次出現開關門：鎖住的門撞不壞，先去踩旁邊的黃色開關。', branch='第一次出現分岔路：一邊有地刺，一邊是逆向輸送帶，自己選。', deck2='高台疊到 3F 了。', deck3='高台疊到 4F 了。',
            crumble='第一次出現崩塌地板：踩過半秒就塌，不要停。', lift='第一次出現升降台：降下來時開上去，會被帶上高台。', dark='第一次出現黑暗區：只看得到身邊一圈。', lowg='第一次出現低重力：滑很遠、拖曳不太有用，跳台飛得更久。',
            chase='第一次出現病毒牆：紅色的牆從後面追上來，被追到就損失一隻陀螺，一路往前衝！')
CHASM_SEGS = {'bridge', 'jumpgap', 'railgap'}
def track(c, plan, mobs_n, mods, mobLv=None, floor=None, mobs_pool=None):
    y = 330; props = [dict(type='boost', x=0, y=280)]; gaps = []; signs = [dict(y=60, txt='START')]; slots = []; ng = 0; ex = dict(decks=[], chasms=[], crumble=[]); starts = []
    for k in plan:
        if k == 'gap':
            if ng >= c['gmax']: k = 'bumpers'
            else: ng += 1
        s = SEGS[k](y, c); props += s['props']; gaps += s['gaps']
        for kk, v in s['ex'].items(): ex[kk] += v
        sg = s['sign']
        if sg and not any(abs(q['y'] - (y - 20)) < 260 for q in signs): signs.append(dict(y=y - 20, txt=sg[0], col=sg[1]))
        starts.append(y); slots.append((y + s['used'] - 40, k)); y += s['used']
    ln = y + 420
    signs.append(dict(y=ln - 330, txt='GOAL', col='#7fdfff'))
    props += [dict(type='boost', x=-0.32, y=ln - 350), dict(type='boost', x=0.32, y=ln - 350)]
    mobs = []; ok = [q for q in slots if q[1] not in ('switch', 'crumble') and q[1] not in CHASM_SEGS]; R.shuffle(ok)
    pool = mobs_pool or c['mobs']
    for i, (sy, k) in enumerate(sorted(ok[:mobs_n])):
        q = R.choice(pool); typ = 'guard' if i % 2 == 0 else 'rush'
        mobs.append(dict(type=typ, x=0 if typ == 'guard' else R.choice([-0.3, 0.3]), y=min(sy, ln - 420), c=q[0], w=q[1], a=q[2]))
    tr = dict(len=ln, mobLv=c['mob'] if mobLv is None else mobLv, floor=floor or c['floor'], signs=signs, gaps=gaps, props=props, mobs=mobs)
    for kk, v in ex.items():
        if v: tr[kk] = v
    for m in mods: # dark / low-gravity stretch over the middle of the road; the chase wall over the whole road
        if m in ('dark', 'lowg'):
            a = starts[max(1, len(starts) // 3)]; b = min(ln - 500, a + R.choice([1000, 1200, 1400]))
            tr[m] = [dict(**{'from': a}, to=b)]; signs.append(dict(y=a - 40, txt='BLACKOUT' if m == 'dark' else 'LOW-G', col='#ff4fd8' if m == 'dark' else '#c9b3ff'))
        if m == 'chase': tr['chase'] = dict(speed=105 + 9 * c['no'], delay=3)
    signs.sort(key=lambda q: q['y'])
    return tr

ARENA = [lambda: dict(type='bumper', at=9, d=0.55), lambda: dict(type='bumper', at=3, d=0.55), lambda: dict(type='barrel', at=10, d=0.45), lambda: dict(type='barrel', at=2, d=0.45),
         lambda: dict(type='laser', at=12, d=0.32, len=150, on=1.2, off=2), lambda: dict(type='magnet', at=6, d=0.3, r=70, power=-1), lambda: dict(type='ice', at=4, d=0.5, r=55),
         lambda: dict(type='wind', at=8, d=0.45, r=60, dir=3, power=0.6), lambda: dict(type='mover', at=6, d=0.25, len=90, move='spin', speed=0.12), lambda: dict(type='spikes', at=9, d=0.5, r=38, on=2, off=2, skin='fire')]
def goal(c, n):
    ps = [dict(type='boost', at=6, d=0.6, dir=12)] + [f() for f in R.sample(ARENA, 3)]
    gs = [dict(type='guard', at=11, d=0.64, c=c['mobs'][0][0], w=c['mobs'][0][1], a=c['mobs'][0][2]), dict(type='guard', at=1, d=0.64, c=c['mobs'][1][0], w=c['mobs'][1][1], a=c['mobs'][1][2])]
    return dict(hp=c['door'] + n * 4, wave=c['wave'], respawn=8, guards=gs, stage=dict(floor=c['floor'], props=ps))
def boss_lv(c, b, n):
    bp = [f() for f in R.sample(ARENA[:4] + ARENA[5:7], 2)]
    m = R.choice(c['mobs'])
    return dict(name=b['name'], c=b['c'], w=b['w'], a=b['a'], diff='normal', lv=b['lv'], hp=b['hp'], size=b.get('size', 1.55), lives=b.get('lives', 1),
                stage=dict(exits=[dict(at=6, type='DEAD', w=46) if b.get('lives', 1) > 1 else dict(at=6, type='DEAD')], ringOut=0.3, floor=c['floor'], props=bp),
                phase2=dict(mobs=[dict(type='guard', at=10, d=0.5, c=m[0], w=m[1], a=m[2])], props=[ARENA[R.choice([4, 7, 8])]()]),
                phase3=dict(props=[dict(type='barrel', at=7.5, d=0.55), dict(type='barrel', at=4.5, d=0.55)]))

# which road mechanics each chapter brings in (introduced one per level on levels 1-4, 6, 7, in this order), the dark / low-g / chase levels, road length
FEAT = {
 1: dict(new=['ramp', 'bumpers', 'deck', 'spikes', 'belt', 'spinner'], base=['boost'], nseg=8, chase=[7], dark=[], lowg=[]),
 2: dict(new=['ice', 'tube', 'bridge', 'portal', 'firewall', 'gap'], base=['slide'], nseg=9, chase=[7], dark=[], lowg=[]),
 3: dict(new=['wind', 'barrels', 'jumpgap', 'turn'], nseg=9, chase=[7], dark=[], lowg=[]),
 4: dict(new=['magnet', 'laser', 'rail', 'railgap'], nseg=10, chase=[7], dark=[], lowg=[]),
 5: dict(new=['switch', 'branch', 'deck2'], nseg=10, chase=[7], dark=[], lowg=[]),
 6: dict(new=['tube', 'portal', 'laser'], nseg=10, chase=[7], dark=[1, 3, 6, 8], lowg=[]),
 7: dict(new=['deck2', 'wind', 'ice'], nseg=11, chase=[7], dark=[], lowg=[0, 2, 5, 6, 8]),
 8: dict(new=['crumble', 'lift', 'barrels'], nseg=11, chase=[7], dark=[], lowg=[]),
 9: dict(new=['bridge', 'railgap', 'magnet', 'gap'], nseg=11, chase=[7], dark=[], lowg=[]),
 10: dict(new=['deck3', 'switch', 'jumpgap'], nseg=11, chase=[5, 7], dark=[2, 6], lowg=[3]),
 11: dict(new=['crumble', 'tube', 'laser'], nseg=11, chase=[7], dark=[0, 2, 4, 7], lowg=[]),
 12: dict(new=['belt', 'magnet', 'crumble', 'lift'], nseg=11, chase=[7], dark=[], lowg=[]),
 13: dict(new=['wind', 'bridge', 'turn', 'spikes'], nseg=11, chase=[7], dark=[], lowg=[]),
 14: dict(new=['deck3', 'tube', 'ice', 'rail'], nseg=11, chase=[7], dark=[], lowg=[1, 3, 5, 7, 9]),
 15: dict(new=['switch', 'railgap', 'deck3', 'crumble'], nseg=11, chase=[5, 7], dark=[3, 8], lowg=[6]),
}
SEEN = []           # every mechanic, in the order it first shows up in the game
INTRO_AT = [0, 1, 2, 3, 5, 6]
CAPS = dict(magnet=1, barrels=2, switch=1, lift=1, deck=2, deck2=1, deck3=1, tube=2, crumble=2, bridge=2, jumpgap=2, railgap=1, firewall=2, branch=1)
def plan_for(c, i, isb):
    F = FEAT[c['no']]; n = c['no']
    known = list(dict.fromkeys(SEEN))  # everything from earlier chapters / levels
    intro = [k for j, k in enumerate(F['new']) if j < len(INTRO_AT) and INTRO_AT[j] <= i]
    theme = list(dict.fromkeys(F['new'][:len(intro)] + [k for k in F['new'] if k in known]))
    pool = [k for k in known if k not in ('chase', 'dark', 'lowg')] + F.get('base', [])
    cnt = F['nseg'] - (2 if isb else 0) + (1 if i == 7 else 0)
    must = F['new'][INTRO_AT.index(i)] if i in INTRO_AT and INTRO_AT.index(i) < len(F['new']) else (R.choice(theme) if theme else None)
    plan = [must] if must else []
    tries = 0
    while len(plan) < cnt:
        tries += 1; k = R.choice(theme) if theme and R.random() < 0.45 else R.choice(pool or ['boost', 'bumpers'])
        if tries > 200: k = R.choice(['boost', 'bumpers'] if n > 1 else ['boost'])
        elif plan.count(k) >= CAPS.get(k, 3): continue
        if sum(p in CHASM_SEGS for p in plan) >= (2 if n < 9 else 3) and k in CHASM_SEGS: continue
        plan.append(k)
    if i in FEAT[n]['chase']: # chase levels are run levels: nothing that makes you stop and ram
        plan = [p if p not in ('firewall', 'barrels', 'switch', 'lift', 'branch') else R.choice(['ramp', 'boost', 'bridge' if n > 1 else 'deck']) for p in plan]
    R.shuffle(plan)
    BLOCK = ('firewall', 'barrels', 'switch', 'lift', 'branch')
    j = 0
    while j < len(plan) - 1: # never make the player stop right after collapsing floor / a chasm (a knock-back would drop them in)
        if plan[j] in ('crumble',) + tuple(CHASM_SEGS) and plan[j + 1] not in ('boost', 'ramp'): plan.insert(j + 1, 'boost') # nothing that bounces you back right after a drop
        elif plan[j] in ('ramp', 'jumpgap') and plan[j + 1] in tuple(CHASM_SEGS) + ('crumble',): plan.insert(j + 1, 'boost')
        j += 1
    if n == 1 and i < 2: plan = [p for p in plan if p != 'spikes']  # 1-1 / 1-2: nothing that drains the spin
    return plan
STAR_KILLS = lambda st, nm, chase: [s if s[0] != 'kills' else (['lives', 3] if chase else ['kills', min(s[1], max(2, nm - 1))]) for s in st]
def level(c, i, L, base=None):
    n = c['no']; lid = f'{n}-{i + 1}'; isb = i + 1 in (5, 9, 10)
    plan = plan_for(c, i, isb)
    F = FEAT[n]; mods = [m for m in ('dark', 'lowg', 'chase') if i in F[m]]
    news = [k for k in dict.fromkeys(plan + mods) if k not in SEEN]
    for k in plan + mods:
        if k not in SEEN: SEEN.append(k)
    nm = 2 if 'chase' in mods else 3 + (i >= 4) + (i >= 7)
    if base: tr = track(c, plan, nm, mods, base['mobLv'], base['floor'], base['mobs'] if len(base['mobs']) >= 2 else None)
    else: tr = track(c, plan, nm, mods)
    feats = []; [feats.append(PN[p]) for p in mods + plan if PN.get(p) and PN[p] not in feats]
    out = dict(id=lid, name=L[0])
    tut = ''.join(EXPL[k] for k in news if k in EXPL)
    if isb: out['desc'] = L[1] + ('　' + tut if tut else '')
    else: out['desc'] = L[1] + '　' + tut + '機關：' + '、'.join(feats[:6]) + '。'
    out['track'] = tr
    if base and isb: out['boss'] = base['boss']
    elif isb: out['boss'] = boss_lv(c, c['bosses'][[5, 9, 10].index(i + 1)], i)
    elif base: out['goal'] = base['goal']
    else: out['goal'] = goal(c, i)
    k3 = len(tr['mobs']); chase = 'chase' in mods
    if base: out['stars'] = STAR_KILLS(base['stars'], k3, chase); out['reward'] = base['reward']
    else:
        st = [['win'], ['lives', 2], R.choice([['kills', min(k3, 3 + (i > 5))], ['lives', 3], ['ex', 2]])] if not isb else [['win'], ['lives', 2], (['ex', 3] if i == 9 else ['lives', 3] if i == 4 else ['kills', 2])]
        out['stars'] = STAR_KILLS(st, k3, chase)
        b0 = c['coin'] + i * c['coin'] // 20
        out['reward'] = dict(first=dict(coins=b0 * (2 if isb else 1) + (c['coin'] if i == 9 else 0), **({'box': 'purple'} if isb else {})), star3=dict(coins=b0 * 6 // 10 * (2 if isb else 1), **({'box': 'white'} if i in (6, 7) else {})))
    if base: out = {k: out[k] for k in ['id', 'name', 'boss', 'desc', 'track', 'goal', 'stars', 'reward'] if k in out}
    return out
W = lambda c, w, a: (c, w, a)
CH = [
 dict(no=6, id='c6', name='第六章・暗網深層', desc='宿主的本體藏在網路深處。虛駭組的地盤到處是傳送門和雷射，被控制的駭客們守在每一層。', bonus=dict(coins=30000, box='purple'),
      floor=['#1f3a5e', '#162a44', '#0d1a2b'], mob=0.9, door=240, wave=4, crack=60, skin='', gmax=1, nseg=7, coin=2400,
      mobs=[W('nova', 'emp', 'forcefield'), W('raven', 'vibrosword', 'afterimage'), W('rat', 'gatling', 'hover'), W('spam', 'smartpistol', 'deflector'), W('twins', 'railgun', 'opticamo')],
      segs=['portal', 'laser', 'ice', 'bumpers', 'spinner', 'boost', 'spikes', 'gap', 'slide'], must=[['portal'], ['laser'], ['ice'], ['portal', 'laser']],
      bosses=[dict(name='亂碼鑽頭・咔啦', c='boss_rat', w='gatling', a='hover', lv=0.86, hp=1.62), dict(name='短路巫毒・諾娃', c='boss_nova', w='emp', a='forcefield', lv=0.88, hp=1.67), dict(name='故障殘影・夜鴉', c='boss_raven', w='vibrosword', a='afterimage', lv=0.88, hp=0.85, lives=2, size=1.6)]),
 dict(no=7, id='c7', name='第七章・夢境迴廊', desc='穿過暗網，來到異哲團打造的夢境。路面會飄、會滑、會把你吹走，夢裡的守門人一個比一個難纏。', bonus=dict(coins=35000, box='purple'),
      floor=['#5e3a6e', '#442a50', '#2b1a33'], mob=0.92, door=245, wave=4, crack=60, skin='', gmax=1, nseg=7, coin=2600,
      mobs=[W('sheep', 'hydrohammer', 'exoskeleton'), W('maiden', 'missilepod', 'plasmaplate'), W('proteus', 'plasmascythe', 'afterimage'), W('theseus', 'vibrosword', 'nanorepair'), W('david', 'railgun', 'titanium')],
      segs=['wind', 'ice', 'portal', 'bumpers', 'magnet', 'spinner', 'boost', 'spikes', 'gap'], must=[['wind'], ['ice', 'wind'], ['magnet'], ['portal']],
      bosses=[dict(name='噩夢囈語・夢', c='boss_sheep', w='hydrohammer', a='exoskeleton', lv=0.88, hp=1.67), dict(name='冷血鐵棺・瑪登', c='boss_maiden', w='missilepod', a='plasmaplate', lv=0.9, hp=1.71), dict(name='惡性擬態・普羅透斯', c='boss_proteus', w='plasmascythe', a='afterimage', lv=0.9, hp=0.85, lives=2, size=1.6)]),
 dict(no=8, id='c8', name='第八章・舊日競技場', desc='夢境的盡頭是一座廢棄的競技場——最早的六位選手在這裡出道，現在他們也被控制了。', bonus=dict(coins=40000, box='purple'),
      floor=['#6e3e2e', '#502d22', '#331c15'], mob=0.94, door=225, wave=3.8, crack=55, skin='fire', gmax=1, nseg=7, coin=2800,
      mobs=[W('assassin', 'vibrosword', 'opticamo'), W('hunter', 'railgun', 'carbonvest'), W('mage', 'emp', 'forcefield'), W('berserker', 'chainaxe', 'powerarmor'), W('guardian', 'hydrohammer', 'titanium')],
      segs=['barrels', 'spinner', 'slide', 'bumpers', 'spikes', 'boost', 'gap', 'laser', 'wind'], must=[['barrels'], ['spinner', 'slide'], ['barrels', 'spikes'], ['gap']],
      bosses=[dict(name='背叛之影・刺客', c='boss_assassin', w='vibrosword', a='opticamo', lv=0.9, hp=1.67), dict(name='失明準星・獵人', c='boss_hunter', w='railgun', a='carbonvest', lv=0.9, hp=1.71), dict(name='扭曲咒環・術士', c='boss_mage', w='emp', a='forcefield', lv=0.92, hp=0.85, lives=2, size=1.6)]),
 dict(no=9, id='c9', name='第九章・王者之路', desc='通往核心的最後一條路。守在路上的是最強的戰士們，每一關都是硬仗。', bonus=dict(coins=45000, box='purple'),
      floor=['#5e4e1f', '#443816', '#2b230d'], mob=0.9, door=225, wave=3.6, crack=55, skin='fire', gmax=1, nseg=7, coin=3000,
      mobs=[W('guardian', 'hydrohammer', 'titanium'), W('berserker', 'chainaxe', 'powerarmor'), W('rex', 'chainaxe', 'powerarmor'), W('erin', 'shotgun', 'reactive'), W('jack', 'railgun', 'opticamo')],
      segs=['magnet', 'laser', 'gap', 'barrels', 'spinner', 'wind', 'boost', 'spikes', 'bumpers', 'ice'], must=[['magnet', 'laser'], ['gap'], ['barrels'], ['wind', 'magnet']],
      bosses=[dict(name='永劫亡魂・不死者', c='boss_undead', w='chainaxe', a='powerarmor', lv=0.76, hp=1.1), dict(name='背誓聖盾・守護者', c='boss_guardian', w='hydrohammer', a='titanium', lv=0.82, hp=1.35), dict(name='血怒狂暴・狂戰士', c='boss_berserker', w='chainaxe', a='powerarmor', lv=0.84, hp=0.7, lives=2, size=1.6)]),
 dict(no=10, id='c10', name='第十章・終焉核心', desc='宿主的核心就在眼前。所有機關、所有被控制的選手全部出動——這是最後一戰。', bonus=dict(coins=60000, box='purple'),
      floor=['#4a1f2e', '#361622', '#220d15'], mob=0.92, door=230, wave=3.6, crack=55, skin='fire', gmax=1, nseg=7, coin=3300,
      mobs=[W('host', 'plasmascythe', 'plasmaplate'), W('twins', 'railgun', 'opticamo'), W('maiden', 'missilepod', 'plasmaplate'), W('raven', 'vibrosword', 'afterimage'), W('tesla', 'emp', 'forcefield'), W('octo', 'gatling', 'deflector')],
      segs=['portal', 'laser', 'magnet', 'wind', 'barrels', 'ice', 'gap', 'spinner', 'spikes', 'bumpers', 'slide'], must=[['portal', 'magnet'], ['laser', 'wind'], ['barrels', 'ice'], ['gap', 'laser']],
      bosses=[dict(name='崩壞重拳・雷克斯', c='boss_rex2', w='hydrohammer', a='exoskeleton', lv=0.92, hp=1.71), dict(name='終末時針・克羅諾', c='boss_chrono2', w='smartpistol', a='afterimage', lv=0.94, hp=1.75), dict(name='覺醒本體・宿主', c='boss_host2', w='plasmascythe', a='plasmaplate', lv=0.94, hp=0.62, lives=3, size=1.75)]),

 dict(no=11, id='c11', name='第十一章・殘響訊號', desc='宿主倒下了，但它的回聲還留在網路裡。被打倒過的選手又開始一個個失控——這次更強。', bonus=dict(coins=70000, box='purple'),
      floor=['#1f2f5e', '#162244', '#0d152b'], mob=0.93, door=235, wave=3.6, crack=55, skin='', gmax=1, nseg=8, coin=3500,
      mobs=[W('spam', 'smartpistol', 'deflector'), W('twins', 'railgun', 'opticamo'), W('raven', 'vibrosword', 'afterimage'), W('nova', 'emp', 'forcefield'), W('chrono', 'smartpistol', 'afterimage')],
      segs=['portal', 'laser', 'ice', 'magnet', 'spinner', 'boost', 'spikes', 'gap', 'bumpers'], must=[['portal', 'laser'], ['ice', 'magnet'], ['laser'], ['portal']],
      bosses=[dict(name='垃圾風暴・彈彈', c='boss_spam2', w='smartpistol', a='deflector', lv=0.88, hp=1.6), dict(name='鏡像故障・零與壹', c='boss_twins2', w='railgun', a='opticamo', lv=0.9, hp=1.65), dict(name='黑羽亂碼・夜鴉', c='boss_raven2', w='vibrosword', a='afterimage', lv=0.9, hp=0.75, lives=2, size=1.6)]),
 dict(no=12, id='c12', name='第十二章・機械墳場', desc='殘響躲進了鐵心幫的報廢工廠。生鏽的機器全被喚醒，磁鐵和炸藥桶堆得到處都是。', bonus=dict(coins=75000, box='purple'),
      floor=['#5e4a3a', '#44352a', '#2b211a'], mob=0.91, door=235, wave=3.6, crack=55, skin='fire', gmax=1, nseg=8, coin=3700,
      mobs=[W('rat', 'gatling', 'hover'), W('rex', 'chainaxe', 'powerarmor'), W('octo', 'gatling', 'deflector'), W('rider', 'chainaxe', 'carbonvest'), W('tesla', 'emp', 'forcefield')],
      segs=['magnet', 'barrels', 'spinner', 'slide', 'laser', 'boost', 'spikes', 'gap', 'bumpers'], must=[['magnet'], ['barrels'], ['magnet', 'laser'], ['spinner', 'slide']],
      bosses=[dict(name='廢鐵鑽地・咔啦', c='boss_rat2', w='gatling', a='hover', lv=0.9, hp=1.65), dict(name='千手深淵・八爪', c='boss_octo2', w='gatling', a='deflector', lv=0.86, hp=1.45), dict(name='雷暴核心・T-9', c='boss_tesla2', w='emp', a='forcefield', lv=0.88, hp=0.65, lives=2, size=1.6)]),
 dict(no=13, id='c13', name='第十三章・荒蕪森域', desc='元森域的森林被殘響汙染，風變得狂暴，荊棘長滿了整條路。', bonus=dict(coins=80000, box='purple'),
      floor=['#3a5e3a', '#2a442a', '#1a2b1a'], mob=0.94, door=240, wave=3.5, crack=55, skin='', gmax=1, nseg=8, coin=3900,
      mobs=[W('cactus', 'grenade', 'reactive'), W('dj', 'missilepod', 'deflector'), W('mechcat', 'vibrosword', 'carbonvest'), W('erin', 'shotgun', 'reactive'), W('jack', 'railgun', 'opticamo')],
      segs=['wind', 'spikes', 'barrels', 'ice', 'bumpers', 'boost', 'gap', 'spinner', 'magnet'], must=[['wind'], ['spikes', 'wind'], ['barrels'], ['ice', 'wind']],
      bosses=[dict(name='劇毒荊冠・刺球', c='boss_cactus2', w='grenade', a='reactive', lv=0.82, hp=1.25), dict(name='噪音狂潮・節拍', c='boss_dj2', w='missilepod', a='deflector', lv=0.92, hp=1.7), dict(name='狂獸利爪・機甲貓咪', c='boss_mechcat2', w='vibrosword', a='opticamo', lv=0.92, hp=0.72, lives=2, size=1.6)]),
 dict(no=14, id='c14', name='第十四章・虛空神殿', desc='異哲團的神殿浮在虛空裡。夢、審判、重生——每一層都是一場試煉。', bonus=dict(coins=85000, box='purple'),
      floor=['#4a2e6e', '#362250', '#211533'], mob=0.92, door=240, wave=3.5, crack=55, skin='', gmax=1, nseg=8, coin=4100,
      mobs=[W('sheep', 'hydrohammer', 'exoskeleton'), W('maiden', 'missilepod', 'plasmaplate'), W('proteus', 'plasmascythe', 'afterimage'), W('theseus', 'vibrosword', 'nanorepair'), W('david', 'railgun', 'titanium')],
      segs=['portal', 'ice', 'wind', 'laser', 'magnet', 'spinner', 'spikes', 'gap', 'bumpers'], must=[['portal', 'ice'], ['laser', 'wind'], ['magnet'], ['portal']],
      bosses=[dict(name='永眠牧歌・夢', c='boss_sheep2', w='hydrohammer', a='exoskeleton', lv=0.92, hp=1.7), dict(name='巨石審判・大衛', c='boss_david2', w='railgun', a='titanium', lv=0.88, hp=1.5), dict(name='千面再生・忒修斯', c='boss_theseus2', w='hydrohammer', a='nanorepair', lv=0.93, hp=0.72, lives=2, size=1.6)]),
 dict(no=15, id='c15', name='第十五章・殘響核心', desc='所有殘響的源頭。最初的通緝犯、最強的盾，還有宿主最後的回聲——這次要徹底結束。', bonus=dict(coins=100000, box='purple'),
      floor=['#5e1f2e', '#441622', '#2b0d15'], mob=0.95, door=245, wave=3.4, crack=60, skin='fire', gmax=1, nseg=8, coin=4500,
      mobs=[W('host', 'plasmascythe', 'plasmaplate'), W('jack', 'railgun', 'opticamo'), W('erin', 'shotgun', 'reactive'), W('berserker', 'chainaxe', 'powerarmor'), W('tesla', 'emp', 'forcefield'), W('raven', 'vibrosword', 'afterimage')],
      segs=['portal', 'laser', 'magnet', 'wind', 'barrels', 'ice', 'gap', 'spinner', 'spikes', 'bumpers', 'slide'], must=[['portal', 'magnet'], ['laser', 'wind'], ['barrels', 'ice'], ['gap', 'laser']],
      bosses=[dict(name='亡命獵手・傑克', c='boss_jack2', w='railgun', a='opticamo', lv=0.92, hp=1.7), dict(name='碎盾狂嵐・艾琳', c='boss_erin2', w='shotgun', a='reactive', lv=0.88, hp=1.5), dict(name='殘響之王・宿主', c='boss_host3', w='plasmascythe', a='plasmaplate', lv=0.94, hp=0.55, lives=3, size=1.8)]),
]
NAMES = {
 6: [('封包隧道', '暗網的入口。傳送門的出口剛好在雷射後面。'), ('防毒網', '一層層雷射柵欄擋住去路，抓空檔或鑽缺口。'), ('冰封資料庫', '冷卻系統過載，整條路都結冰了。'), ('迴圈陷阱', '傳送門和雷射交錯，走錯會繞回原地。'),
     ('鼠窩伺服器', 'BOSS 是被控制的咔啦：它會「鑽地」——鑽進地下，從你背後冒出來往出口撞。看到地上一路冒土，就離開出口前方。建議金卡 3 星。'),
     ('殭屍網路', '一大群被感染的陀螺守在路上。'), ('鏡像節點', '每段路都有傳送門分岔，挑對路比較好走。'), ('深層防火牆', '第六章最難的賽道，過了這裡就是連續兩個 BOSS。'),
     ('短路變電箱', 'BOSS 是被控制的諾娃：「電路陷阱」會在你身邊佈下好幾格電路，亮起後踩到會麻痺。陷阱剛放下時還沒通電，趁那時候離開。建議金卡 3 星。'),
     ('全息鴉巢', '第六章最終關。BOSS 是被控制的夜鴉（兩條血）：會叫出全息分身，接著消失並從你背後出現。分身打幾下就碎。建議金卡 3 星。')],
 7: [('雲上步道', '夢境的入口，強風把雲吹得到處跑。'), ('滑行之夢', '冰面和強風一起出現，一不小心就滑出去。'), ('磁力搖籃', '磁鐵像搖籃一樣把你晃來晃去。'), ('失重花園', '傳送門把你送到意想不到的地方。'),
     ('羊群牧場', 'BOSS 是被控制的夢：「入夢」會在你周圍飄出粉紅色的夢境雲，待在雲裡太久會睡著。雲剛出現時還沒成形，趁那時候離開。建議金卡 3 星。'),
     ('迷途回聲', '同一條路好像走過好幾次？'), ('聖母長廊', '雕像們排成一列守著走廊。'), ('夢醒時分', '第七章最難的賽道，過了這裡就是連續兩個 BOSS。'),
     ('鐵棺禮拜堂', 'BOSS 是被控制的瑪登：「鐵之擁抱」會衝過來，被碰到就會被抱住、持續扣血。它身邊出現紫色光圈時要拉開距離。建議金卡 3 星。'),
     ('擬態之間', '第七章最終關。BOSS 是被控制的普羅透斯（兩條血）：「擬態」會輪流使出前面 BOSS 的招式——撒刺、音浪、落雷、投石、電路、夢境雲。看它頭上的提示反應。建議金卡 3 星。')],
 8: [('觀眾席廢墟', '舊競技場的看台塌了，到處都是炸藥桶。'), ('刀鋒迴廊', '旋轉擋板和推板一路排開。'), ('火線', '火焰地刺和炸藥桶夾著前進。'), ('斷層跑道', '跑道裂成好幾段，左右都有缺口。'),
     ('影之試煉', 'BOSS 是被控制的刺客：「影襲」會消失，再從你背後出現往出口撞。消失的時候別停在出口前面。建議金卡 3 星。'),
     ('練習場', '最早的練習場地，擋板全部重新啟動。'), ('冠軍走道', '歷屆冠軍的陀螺都在這裡等你。'), ('閉幕式', '第八章最難的賽道，過了這裡就是連續兩個 BOSS。'),
     ('狩獵禁區', 'BOSS 是被控制的獵人：「鎖定標記」讓你受傷加重、EX 封鎖，接著一支接一支連射。看到紅色虛線就橫向閃開。建議金卡 3 星。'),
     ('咒環舞台', '第八章最終關。BOSS 是被控制的術士（兩條血）：「環域扭曲」會從身上放出青色扭曲波，碰到會被彈開並暈眩。建議金卡 3 星。')],
 9: [('鋼鐵大道', '磁鐵和雷射守著王者之路的入口。'), ('懸崖邊緣', '缺口一個接一個，牆邊不能待。'), ('戰火迴廊', '炸藥桶和防火牆層層堆起。'), ('暴風關口', '強風把你往磁場裡吹。'),
     ('不死者墓碑', 'BOSS 是被控制的不死者：會撒出白骨地刺，而且第一次被打倒會「亡者回魂」，以兩成半血復活。留一點力氣打第二次。建議金卡 3 星。'),
     ('鐵壁', '守門型敵人排成一道牆。'), ('王者試煉', '所有機關輪番上陣。'), ('最後的走廊', '第九章最難的賽道，過了這裡就是連續兩個 BOSS。'),
     ('背誓聖堂', 'BOSS 是被控制的守護者：「聖域壁壘」2.5 秒內完全不受傷，碰到會被彈開，結束時放出黃色震波。護盾期間別硬撞，等震波過了再打。建議金卡 3 星。'),
     ('血怒王座', '第九章最終關。BOSS 是被控制的狂戰士（兩條血）：「狂暴衝鋒」連撞三次，一次比一次痛。撞牆會暈眩，引它去撞牆。建議金卡 3 星。')],
 10: [('核心外環', '終焉核心的外圍。前面所有的機關都在這裡。'), ('記憶迴廊', '走過的每一章，都在這條路上重現。'), ('寄生管線', '被感染的管線到處是陷阱。'), ('崩壞之門', '核心的大門前，防火牆一道比一道硬。'),
      ('重拳回歸', 'BOSS 是再次被控制的雷克斯：輪流使出「連環重砸」和「狂暴衝鋒」。地上的紅圈是重砸、閃紅光是衝鋒。建議金卡 3 星。'),
      ('倒數計時', '核心開始倒數，賽道越來越危險。'), ('全員集合', '所有陣營的被控制選手都來了。'), ('最終防衛線', '全遊戲最難的賽道。過了這裡就是最後兩個 BOSS。'),
      ('時間盡頭', 'BOSS 是再次被控制的克羅諾：輪流使出「時間停止」「扭曲波」「落雷」。時鐘圈、青色波、光圈，看到哪個就躲哪個。建議金卡 3 星。'),
      ('終焉核心', '最終關。BOSS 是宿主的真正樣子「覺醒本體」（三條血）：寄生、落雷、電路陷阱、夢境雲、音浪、投石、扭曲波全部會用。三隻陀螺都要強，ASSIST 留到最後。建議金卡 3 星。')],

 11: [('廢棄伺服器', '殘響的第一個訊號就從這裡發出。'), ('冰封快取', '冷卻失控，整條路結了冰。'), ('雙重驗證', '每道雷射都要通過兩次。'), ('迴圈地獄', '傳送門一個接一個，小心繞回原點。'),
      ('廣告墳場', 'BOSS 是再次被控制的彈彈：輪流使出「彈窗洗版」和「電路陷阱」。被廣告窗圍住時，小心腳下的電路。建議金卡 3 星。'),
      ('封包洪流', '大量被感染的封包衝過來。'), ('鏡面走廊', '到處都是反射的影子。'), ('核心防火牆', '第十一章最難的賽道。'),
      ('雙生故障', 'BOSS 是再次被控制的零與壹：分身和全息影像同時出現，真身會從背後突襲。建議金卡 3 星。'),
      ('黑羽之巢', '第十一章最終關。BOSS 是再次被控制的夜鴉（兩條血）：輪流使出全息分身、影襲和落雷。建議金卡 3 星。')],
 12: [('報廢產線', '生鏽的產線又開始動了。'), ('磁力廢墟', '一整片磁鐵把你往廢鐵堆吸。'), ('炸藥倉', '炸藥桶堆得比人還高。'), ('絞碎機', '旋轉擋板和推板排成一列。'),
      ('鼠洞', 'BOSS 是再次被控制的咔啦：「鑽地」從背後冒出，衝過的地方還會起火。別停在出口前面。建議金卡 3 星。'),
      ('廢油池', '地上到處是滑溜的油漬和火焰。'), ('起重機陣', '磁鐵吊臂到處移動。'), ('熔爐深處', '第十二章最難的賽道。'),
      ('深淵水槽', 'BOSS 是再次被控制的八爪：輪流使出「觸手拖拉」和「鐵之擁抱」。拉開距離，別被碰到。建議金卡 3 星。'),
      ('雷暴發電廠', '第十二章最終關。BOSS 是再次被控制的 T-9（兩條血）：落雷、電路陷阱、扭曲波輪流來。建議金卡 3 星。')],
 13: [('枯木林道', '風把枯枝吹得到處都是。'), ('荊棘迷宮', '地刺一片接一片。'), ('毒沼', '強風會把你吹進毒刺。'), ('冰封湖面', '湖面結冰，風還在吹。'),
      ('毒刺花園', 'BOSS 是再次被控制的刺球：「撒刺」加上「入夢」，被刺圍住時還會想睡。建議金卡 3 星。'),
      ('狂風峽谷', '兩邊的風輪流吹。'), ('野獸小徑', '一大群野獸陀螺守在路上。'), ('森林之心', '第十三章最難的賽道。'),
      ('噪音祭典', 'BOSS 是再次被控制的節拍：音浪裡混著扭曲波，碰到就暈。抓空檔穿過去。建議金卡 3 星。'),
      ('獸王巢穴', '第十三章最終關。BOSS 是再次被控制的機甲貓咪（兩條血）：連續撲殺、狂暴衝鋒、背後突襲。建議金卡 3 星。')],
 14: [('浮空階梯', '神殿的入口浮在虛空中。'), ('鏡之迴廊', '傳送門和冰面交錯。'), ('審判之路', '雷射柵欄層層把關。'), ('引力祭壇', '磁鐵像祭壇一樣守著路。'),
      ('永眠牧場', 'BOSS 是再次被控制的夢：夢境雲、白刺和音浪輪流來，待在雲裡會睡著。建議金卡 3 星。'),
      ('虛空裂縫', '路面裂成好幾段。'), ('信徒長廊', '異哲團的信徒擋在每個轉角。'), ('至聖所', '第十四章最難的賽道。'),
      ('巨石法庭', 'BOSS 是再次被控制的大衛：鎖定標記、投石、連環重砸三段審判。建議金卡 3 星。'),
      ('重生之間', '第十四章最終關。BOSS 是再次被控制的忒修斯（兩條血）：重組回血、聖域護盾、落雷。重組時要打斷它。建議金卡 3 星。')],
 15: [('最後的入口', '殘響核心的大門。'), ('記憶殘片', '前面所有章節的機關都在這裡重現。'), ('通緝令', '整條路都貼滿了你的通緝令。'), ('碎盾之門', '防火牆一道比一道硬。'),
      ('獵手之夜', 'BOSS 是再次被控制的傑克：全場通緝、鎖定標記、投石輪流來。建議金卡 3 星。'),
      ('倒數歸零', '核心開始崩壞，賽道越來越危險。'), ('全員回聲', '所有被控制過的選手都在這裡。'), ('最後的防線', '全遊戲最難的賽道，過了這裡就是最後兩個 BOSS。'),
      ('狂嵐盾陣', 'BOSS 是再次被控制的艾琳：狂暴衝鋒、聖域護盾、連環重砸。護盾期間別硬撞。建議金卡 3 星。'),
      ('殘響之王', '最終關。BOSS 是宿主最後的回聲「殘響之王」（三條血）：前面所有 BOSS 的招式它都會用。三隻陀螺都要強。建議金卡 3 星。')],
}
# chapters 1-5: names, BOSSes, goals, stars and rewards come from tools/base_1_5.json; these are the new road flavour lines
FLAVOR = {
 '1-1': '第一條賽道。往後拉、放開發射，自動彈牆，飛行中拖曳可以微調方向。衝進終點的圓形場後，用力撞最上面的門（撞越快扣越多），門破了衝進去就過關。門每隔幾秒會放衝擊波把你彈開，還有守衛。',
 '1-2': '整條街都是彈力柱，撞上去會被彈開。', '1-3': '斷掉的高架橋被搭成了一層層的平台。', '1-4': '夜市的地上埋滿了會冒出來的地刺。',
 '1-6': '大樓天台的臨時賽道，輸送帶把你一路往前送。', '1-7': '一路都是轉個不停的擋板。', '1-8': '第一章最長的一條。病毒牆從後面追上來，過了這裡就是連續兩個 BOSS。',
 '2-1': '資料中心的冷卻液漏了一地。', '2-2': '粉紅色的管道把你直接吸到前面去。', '2-3': '整段路都斷線了，只剩幾條細細的橋。', '2-4': '空間被打出了洞，WARP 門到處都是。',
 '2-6': '一道道防火牆擋在路上。', '2-7': '牆也斷了，路邊到處是缺口。', '2-8': '第二章最難的賽道，病毒牆緊追在後。過了這裡就是連續兩個 BOSS。',
 '3-1': '荒野的風口，風大得站不穩。', '3-2': '沒人管的炸藥桶堆滿了倉庫。', '3-3': '峽谷中間斷了，只能用跳台飛過去。', '3-4': '舊風車的底座變成了旋轉圓盤。',
 '3-6': '強風、炸藥桶和深淵混在一起。', '3-7': '大群野生陀螺藏在峽谷裡。', '3-8': '第三章最難的賽道，病毒牆緊追在後。過了這裡就是連續兩個 BOSS。',
 '4-1': '磁鐵吊臂會把你吸過去。', '4-2': '雷射柵欄一亮一滅，工廠在加班。', '4-3': '頭頂的黃色滑軌是送貨用的高速通道。', '4-4': '滑軌架在熔爐上方，掉下去就完了。',
 '4-6': '輸送帶把你往牆邊的缺口送。', '4-7': '工人陀螺全都暴動了。', '4-8': '第四章最難的賽道，病毒牆緊追在後。過了這裡就是連續兩個 BOSS。',
 '5-1': '聖所的大門被鎖住了。', '5-2': '聖所的走廊分成兩條路。', '5-3': '高台一層一層往上疊，像祭壇一樣。', '5-4': '前面所有的機關都出現在迷宮裡。',
 '5-6': '雷射、磁鐵、滑軌輪番上陣。', '5-7': '異哲團的信徒陀螺一湧而上。', '5-8': '第五章最難的賽道，病毒牆緊追在後。過了這裡就是連續兩個 BOSS。',
}
BASE_CFG = {1: dict(mob=0, door=100, wave=5, crack=35, skin='', gmax=1, coin=300), 2: dict(mob=0.4, door=120, wave=4.6, crack=40, skin='', gmax=1, coin=600),
            3: dict(mob=0.6, door=160, wave=4.4, crack=45, skin='', gmax=1, coin=1000), 4: dict(mob=0.8, door=200, wave=4.2, crack=50, skin='fire', gmax=1, coin=1400),
            5: dict(mob=0.9, door=240, wave=4, crack=55, skin='', gmax=1, coin=1800)}
def main():
    base = json.load(open(os.path.join(HERE, 'base_1_5.json'), encoding='utf8'))
    out = []
    for b in base:
        n = b['no']; mobs = []
        for l in b['levels']: mobs += [tuple(m) for m in l['mobs'] if tuple(m) not in mobs]
        c = dict(no=n, id=b['id'], name=b['name'], desc=b['desc'], bonus=b['bonus'], floor=b['levels'][0]['floor'], mobs=mobs, **BASE_CFG[n])
        lv = []
        for i, L in enumerate(b['levels']):
            fl = L.get('desc') if L.get('boss') else FLAVOR[L['id']]
            lv.append(level(c, i, (L['name'], fl), L))
        out.append('  ' + js(dict(id=c['id'], no=n, name=c['name'], desc=c['desc'], bonus=c['bonus'], levels=lv)) + ',')
    for c in CH:
        lv = [level(c, i, NAMES[c['no']][i]) for i in range(10)]
        out.append('  ' + js(dict(id=c['id'], no=c['no'], name=c['name'], desc=c['desc'], bonus=c['bonus'], levels=lv)) + ',')
    txt = '\n'.join(out)
    if '--print' in sys.argv: print(txt); return
    f = os.path.join(HERE, '..', 'js', 'chapters.js'); h = open(f, encoding='utf8').read()
    import re; txt = re.sub(r'建議[^。\']*。', '', txt)  # v0.53.5: no tier recommendations in the stage text (difficulty is now eased per chapter)
    i = h.index("  { id: 'c1'"); j = h.index('\n];\n', i); open(f, 'w', encoding='utf8').write(h[:i] + txt + h[j:]); print('chapters 1-15 written to js/chapters.js')
main()
