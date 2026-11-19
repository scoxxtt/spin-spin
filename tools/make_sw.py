# Rebuilds sw.js: cache name from GAME_VERSION + list of files to keep offline. Run after every version bump or new portrait.
import os, re
root = os.path.join(os.path.dirname(__file__), '..'); os.chdir(root)
v = re.search(r"const GAME_VERSION = '([^']+)'", open('index.html', encoding='utf8').read()).group(1)
arts = sorted('art/portraits/' + f for f in os.listdir('art/portraits') if f.endswith('.jpg'))
files = ['./', 'index.html', 'js/assets.js', 'js/chapters.js', 'manifest.webmanifest', 'icons/icon-192.png', 'icons/icon-512.png', 'icons/icon-180.png'] + arts
tpl = open('sw.js', encoding='utf8').read()
tpl = re.sub(r"const CACHE = '[^']*';", "const CACHE = 'spin-%s';" % v, tpl)
tpl = re.sub(r"const FILES = \[.*?\];", "const FILES = %r;" % files, tpl, flags=re.S)
open('sw.js', 'w', encoding='utf8').write(tpl); print('sw.js', v, len(files), 'files')
