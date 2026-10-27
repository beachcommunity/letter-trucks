"""Generate every voice line with OpenRouter TTS, check each take with two listener models,
then trim, loudness-normalize and encode the keepers to voice/final/<key>.mp3.

Key comes from OPENROUTER_API_KEY (never printed). Usage (from the voice/ folder or anywhere):
  python3 voice/tts_gen.py [--only key1,key2] [--takes 4] [--redo]
"""
import os, sys, json, base64, re, time, subprocess, argparse, threading
import concurrent.futures as cf
import warnings; warnings.filterwarnings('ignore')
import requests, numpy as np, soundfile as sf, pyloudnorm as pyln

V = os.path.dirname(os.path.abspath(__file__))
KEY = os.environ.get('OPENROUTER_API_KEY', '').strip()
MODEL = os.environ.get('TTS_MODEL', 'google/gemini-3.8-flash-tts')
VOICE = os.environ.get('TTS_VOICE', 'Charon')
STYLE = os.environ.get('TTS_STYLE', (
    "Warm, cheerful preschool teacher talking to a toddler who is playing a truck game. "
    "Clear and a little slow, smiling, never rushed. A capital letter on its own like 'B!' is the letter's name. "
    "A pattern like 'b-b-bus' means: say the letter's short phonics sound twice (for b: a quick 'b', not 'bee'), then the word."))
LISTENERS = ['google/gemini-3.8-flash', 'qwen/qwen3.8-omni-flash']
API = 'https://openrouter.ai/api/v1'
RAW, FINAL, ORIG = os.path.join(V, 'raw'), os.path.join(V, 'final'), os.path.join(V, 'originals')
for d in (RAW, FINAL, ORIG): os.makedirs(d, exist_ok=True)
H = lambda: {'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json', 'HTTP-Referer': 'https://claude.ai', 'X-Title': 'Letter Trucks'}
lock = threading.Lock()
ALL_TAKES = False

BEAR_STYLE = ("A sweet, cheerful little bear cub talking to a toddler in a truck game. Gentle, warm, a little slow, smiling. "
    "A capital letter on its own like 'B!' is the letter's name. "
    "A pattern like 'b-b-bus' means: say the letter's short phonics sound twice (for b: a quick 'b', not 'bee'), then the word.")
VOICES = json.load(open(os.path.join(V, 'voices.json'))) if os.path.exists(os.path.join(V, 'voices.json')) else {}
def tts(text, key=None):
    voice = VOICES.get(key, VOICE); style = BEAR_STYLE if key in VOICES else STYLE
    for attempt in range(4):
        r = requests.post(f'{API}/audio/speech', headers=H(), timeout=120,
                          json={'model': MODEL, 'input': text, 'voice': voice, 'instructions': style, 'response_format': 'pcm'})
        if r.status_code == 200 and r.headers.get('content-type', '').startswith('audio'):
            return r.content
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(3 + attempt * 5); continue
        raise RuntimeError(f'tts {r.status_code}: {r.text[:300]}')
    raise RuntimeError('tts kept failing')

CHECK = """Listen to this short clip from a toddler phonics game.
The script was: "{text}"
Rules for the script: a capital letter on its own (like "B!") is said as the letter NAME ("bee").
A pattern like "b-b-bus" means the speaker says the letter's SOUND twice (for b a short "b", for s a hissy "sss", for a the vowel in "apple"), then the word.
Reply with JSON only, no code fence:
{{"transcript": "<what you hear>", "matches_script": true or false, "sounds_ok": true or false or null, "problems": "<short>"}}
matches_script: every word in the script is spoken, in order, with nothing added or skipped (ignore punctuation).
sounds_ok: every repeated letter bit was a phonics sound, not the letter name. null if the script has no such pattern."""

def listen(path, text, model):
    b64 = base64.b64encode(open(path, 'rb').read()).decode()
    body = {'model': model, 'temperature': 0, 'messages': [{'role': 'user', 'content': [
        {'type': 'text', 'text': CHECK.format(text=text)},
        {'type': 'input_audio', 'input_audio': {'data': b64, 'format': 'wav'}}]}]}
    for attempt in range(4):
        r = requests.post(f'{API}/chat/completions', headers=H(), json=body, timeout=120)
        if r.status_code == 200:
            out = r.json()['choices'][0]['message']['content'] or ''
            m = re.search(r'\{.*\}', out, re.S)
            try: return json.loads(m.group(0)) if m else {'transcript': out, 'matches_script': False, 'sounds_ok': False, 'problems': 'no json'}
            except Exception: return {'transcript': out, 'matches_script': False, 'sounds_ok': False, 'problems': 'bad json'}
        if r.status_code in (429, 500, 502, 503, 504): time.sleep(3 + attempt * 5); continue
        return {'transcript': '', 'matches_script': False, 'sounds_ok': False, 'problems': f'http {r.status_code}'}
    return {'transcript': '', 'matches_script': False, 'sounds_ok': False, 'problems': 'listener failed'}

def score(verdicts, has_sound):
    ok_words = sum(bool(v.get('matches_script')) for v in verdicts)
    ok_snd = sum((v.get('sounds_ok') is True) or (not has_sound and v.get('sounds_ok') in (None, True)) for v in verdicts)
    return ok_words + ok_snd

def squeeze_pauses(y, sr, keep=0.32, thr_db=-40):
    # long gaps between words make the game feel slow: cap every internal pause at `keep` seconds
    n = int(0.01 * sr); fr = np.array([np.sqrt(np.mean(y[i:i + n] ** 2)) for i in range(0, len(y) - n, n)]) + 1e-9
    quiet = 20 * np.log10(fr / fr.max()) < thr_db
    out, i, last = [], 0, 0
    while i < len(quiet):
        if quiet[i]:
            j = i
            while j < len(quiet) and quiet[j]: j += 1
            if (j - i) * 0.01 > keep and i > 0 and j < len(quiet):
                a, b = i * n, j * n; half = int(keep * sr / 2)
                out.append(y[last:a + half]); last = b - half
            i = j
        else: i += 1
    out.append(y[last:])
    if len(out) == 1: return y
    xf = int(0.008 * sr); res = out[0]
    for seg in out[1:]:
        if len(res) > xf and len(seg) > xf:
            ramp = np.linspace(0, 1, xf); res = np.concatenate([res[:-xf], res[-xf:] * (1 - ramp) + seg[:xf] * ramp, seg[xf:]])
        else: res = np.concatenate([res, seg])
    return res

def finish(raw_path, out_path):
    wav = raw_path[:-4] + '_fin.wav'
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', raw_path, '-ac', '1', '-ar', '24000',
                    '-af', 'highpass=f=70,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.08,areverse',
                    wav], check=True)
    y, sr = sf.read(wav)
    y = squeeze_pauses(y, sr)
    meter = pyln.Meter(sr)
    try: y = pyln.normalize.loudness(y, meter.integrated_loudness(y), -17.0)
    except Exception: pass
    pk = np.abs(y).max() or 1
    if pk > 0.89: y = y * (0.89 / pk)
    y = np.concatenate([np.zeros(int(0.03 * sr)), y, np.zeros(int(0.06 * sr))])
    sf.write(wav, y, sr)
    # keep a 56k original, and ship a slightly faster (atempo 1.1), smaller 40k copy in the game
    orig = os.path.join(ORIG, os.path.basename(out_path))
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', wav, '-c:a', 'libmp3lame', '-b:a', '56k', orig], check=True)
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', orig, '-af', 'atempo=1.1', '-ac', '1', '-ar', '24000', '-c:a', 'libmp3lame', '-b:a', '40k', out_path], check=True)

def do_line(key, text, takes, log):
    has_sound = bool(re.search(r'\b([a-z]+)-\1-', text, re.I)) or ', ks, ks' in text
    best = None
    for t in range(takes):
        raw = os.path.join(RAW, f'{key}__{t}.wav')
        try:
            pcm = tts(text, key)
            open(raw[:-4] + '.pcm', 'wb').write(pcm)
            subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-f', 's16le', '-ar', '24000', '-ac', '1', '-i', raw[:-4] + '.pcm', raw], check=True)
        except Exception as e:
            log.append({'key': key, 'take': t, 'error': str(e)}); continue
        with cf.ThreadPoolExecutor(2) as ex:
            verdicts = list(ex.map(lambda m: listen(raw, text, m), LISTENERS))
        s = score(verdicts, has_sound)
        rec = {'key': key, 'take': t, 'score': s, 'verdicts': verdicts}
        log.append(rec)
        if best is None or s > best[0]: best = (s, raw, verdicts)
        if s == 2 * len(LISTENERS) and not ALL_TAKES: break
    if best:
        finish(best[1], os.path.join(FINAL, f'{key}.mp3'))
        return key, best[0], best[2]
    return key, -1, None

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--only'); ap.add_argument('--takes', type=int, default=4); ap.add_argument('--redo', action='store_true'); ap.add_argument('--workers', type=int, default=6)
    ap.add_argument('--all-takes', action='store_true')
    a = ap.parse_args()
    globals()['ALL_TAKES'] = a.all_takes
    if not KEY: sys.exit('OPENROUTER_API_KEY not set')
    lines = json.load(open(os.path.join(V, 'lines.json')))
    keys = a.only.split(',') if a.only else list(lines)
    if not a.redo: keys = [k for k in keys if not os.path.exists(os.path.join(FINAL, f'{k}.mp3'))]
    print(f'{len(keys)} lines, model {MODEL}, voice {VOICE}', flush=True)
    log, results = [], []
    with cf.ThreadPoolExecutor(a.workers) as ex:
        futs = [ex.submit(do_line, k, lines[k], a.takes, log) for k in keys]
        for f in cf.as_completed(futs):
            k, s, v = f.result(); results.append((k, s))
            tr = ' | '.join((x or {}).get('transcript', '')[:60] for x in (v or []))
            print(f'{k:14s} score {s}/4  {tr}', flush=True)
    logp = os.path.join(V, 'log.json')
    old = json.load(open(logp)) if os.path.exists(logp) else []
    json.dump(old + log, open(logp, 'w'), indent=1)
    weak = sorted(k for k, s in results if s < 4)
    print('done.', len(results) - len(weak), 'clean,', len(weak), 'weak:', ','.join(weak))
