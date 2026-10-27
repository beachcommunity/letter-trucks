"""Build the game: src/template.html + pictures + voice clips -> dist/letter-trucks.html (one self-contained file).
Usage: python3 build.py   (then `node --check build/check.js` to syntax-check the script)"""
import base64, json, os, glob
R = os.path.dirname(os.path.abspath(__file__))
b64 = lambda p: base64.b64encode(open(p, 'rb').read()).decode()
# one picture per letter (Twemoji SVGs, CC BY 4.0; the igloo is drawn for this game)
pics = {os.path.basename(p)[:-4]: 'data:image/svg+xml;base64,' + b64(p) for p in glob.glob(f'{R}/src/pics/*.svg')}
pics = dict(sorted(((('i' if k == 'igloo' else k), v) for k, v in pics.items() if len(k) == 1 or k == 'igloo')))
lines = json.load(open(f'{R}/voice/lines.json'))
voice = {}
for f in sorted(glob.glob(f'{R}/voice/final/*.mp3')):
    k = os.path.basename(f)[:-4]
    if k in lines: voice[k] = 'data:audio/mpeg;base64,' + b64(f)
credits_txt = open(f'{R}/voice/credits.txt').read().strip()
html = open(f'{R}/src/template.html').read()
for k, v in {'__LINES__': lines, '__VOICE__': voice, '__PICS__': pics, '__CREDITS__': credits_txt}.items():
    html = html.replace(k, json.dumps(v))
os.makedirs(f'{R}/dist', exist_ok=True); os.makedirs(f'{R}/build', exist_ok=True)
open(f'{R}/dist/letter-trucks.html', 'w').write(html)
open(f'{R}/build/check.js', 'w').write(html.split('<script>')[1].split('</script>')[0])
missing = sorted(set(lines) - set(voice))
print('built', round(len(html) / 1024), 'KB,', len(voice), 'voice clips of', len(lines), ('| missing: ' + ','.join(missing)) if missing else '')
