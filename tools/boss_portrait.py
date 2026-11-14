# "controlled" BOSS portrait: forehead sinks into shadow, eyes burn red. usage: boss_pt.py name x1 y1 x2 y2 (eye centres on the 256px portrait)
import sys, numpy as np
from PIL import Image
def make(name, eyes, src='/home/claude/spin-spin/art/portraits', out='/home/claude/spin-spin/art/portraits'):
    S = 2; im = Image.open(f'{src}/{name}.jpg').convert('RGB').resize((256 * S, 256 * S), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32) / 255; H, W = a.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); eyes = [(x * S, y * S) for x, y in eyes]
    ey = sum(e[1] for e in eyes) / len(eyes)
    g = a.mean(axis=2, keepdims=True); a = g + (a - g) * 0.6; a *= np.array([0.80, 0.70, 0.86])          # drained, cold cast
    t = np.clip((ey + 16 * S - yy) / (ey + 16 * S), 0, 1); sh = np.clip((t * t * (3 - 2 * t)) ** 0.55 * 1.05, 0, 0.985)       # shadow: black at the top, gone just under the eyes
    a = a * (1 - sh[..., None]) + np.array([0.03, 0.0, 0.05]) * sh[..., None]
    v = np.clip(np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2)) - 0.72, 0, 1) * 1.6                 # red creeping in from the frame
    a = a * (1 - v[..., None] * 0.55) + np.array([0.75, 0.02, 0.12]) * v[..., None] * 0.45
    glow = np.zeros((H, W), np.float32); core = np.zeros((H, W), np.float32)
    for x, y in eyes:
        d2 = (xx - x) ** 2 + (yy - y) ** 2
        glow += np.exp(-d2 / (2 * (11 * S) ** 2)) * 0.85 + np.exp(-(((xx - x) / (26 * S)) ** 2 + ((yy - y) / (3.2 * S)) ** 2)) * 0.9   # halo + horizontal flare
        core += np.exp(-(((xx - x) / (5.2 * S)) ** 2 + ((yy - y) / (3.4 * S)) ** 2) * 1.2)
    glow = np.clip(glow, 0, 1)[..., None]; core = np.clip(core, 0, 1)[..., None]
    a = 1 - (1 - a) * (1 - glow * np.array([1.0, 0.10, 0.16]))                                                # screen
    a = a * (1 - core) + np.array([1.0, 0.86, 0.80]) * core
    Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).resize((256, 256), Image.LANCZOS).save(f'{out}/boss_{name}.jpg', quality=88)
if __name__ == '__main__':
    n = sys.argv[1]; v = list(map(float, sys.argv[2:])); make(n, [(v[i], v[i + 1]) for i in range(0, len(v), 2)], )
