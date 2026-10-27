"""For the short-vowel lines, choose the take whose repeated vowel sits closest to the target vowel,
among takes the listeners passed. Then finish (trim/normalize/encode) the chosen take."""
import json, os, glob, sys, subprocess, numpy as np, soundfile as sf
os.chdir(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, 'ana'); from seg import segments, formants
import tts_gen
VOICES = json.load(open('voices.json'))
T = {'a': (820, 1800), 'e': (600, 1850), 'i': (430, 2000), 'o': (760, 1250), 'u': (620, 1200)}
log = json.load(open('log.json')) if os.path.exists('log.json') else []
scores = {}
for r in log:
    if 'score' in r: scores[(r['key'], r['take'])] = r['score']
def vowel_F(path, key):
    y, sr = sf.read(path); y = y.astype(float) * 32767
    segs = segments(y, sr, thr_db=-35, minsil=0.06)
    cand = [(a, b) for a, b in segs if 0.06 <= b - a <= 0.45]
    out = []
    for a, b in cand:
        fs = []
        for m in np.linspace(a + (b - a) * .3, a + (b - a) * .7, 5):
            F = formants(y[int((m - .0125) * sr):int((m + .0125) * sr)], sr)
            if len(F) >= 2: fs.append(F[:2])
        if fs: out.append(np.median(np.array(fs), axis=0))
    return out
KINDS = sys.argv[1].split(',') if len(sys.argv) > 1 else ['box', 'order0', 'order1', 'yay', 'say', 'where']
res = {}
for l in 'aeiou':
    for kind in KINDS:
        key = f'{kind}_{l}'; best = None
        for p in sorted(glob.glob(f'raw/{key}__*.wav')):
            if p.endswith('_fin.wav'): continue
            t = int(p.rsplit('__', 1)[1].split('.')[0]); sc = scores.get((key, t), 0)
            if kind == 'where':
                d, Fs = 0.0, []
            else:
                Fs = vowel_F(p, key)
                if not Fs: continue
                f = 1.17 if key in VOICES else 1.0   # the bear voice is higher: scale the vowel targets
                t1, t2 = T[l][0] * f, T[l][1] * f
                ds = sorted(abs(F[0] - t1) / t1 + abs(F[1] - t2) / t2 for F in Fs)
                d = float(np.mean(ds[:2]))   # the two repeated sounds should be the closest matches
            cost = d + (4 - sc) * 0.25
            line = f'{key} take{t} listen{sc}/4 dist {d:.2f}'
            if best is None or cost < best[0]: best = (cost, p, line)
        if best:
            res[key] = best[2]
            tts_gen.finish(best[1], f'final/{key}.mp3')
for k, v in res.items(): print(v)
