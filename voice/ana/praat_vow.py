"""Formants with Praat (Burg). For each clip: speech segments, median F1/F2 over each segment's middle."""
import sys, numpy as np, parselmouth, soundfile as sf
sys.path.insert(0, 'ana'); from seg import segments
def seg_formants(path, maxf):
    snd = parselmouth.Sound(path)
    y = snd.values[0] * 32767; sr = int(snd.sampling_frequency)
    fm = snd.to_formant_burg(time_step=0.005, max_number_of_formants=5, maximum_formant=maxf, window_length=0.025)
    out = []
    for a, b in segments(y, sr, thr_db=-35, minsil=0.06):
        ts = np.linspace(a + (b - a) * 0.3, a + (b - a) * 0.7, 9)
        f1 = [fm.get_value_at_time(1, t) for t in ts]; f2 = [fm.get_value_at_time(2, t) for t in ts]
        f1 = [v for v in f1 if v == v]; f2 = [v for v in f2 if v == v]
        if f1 and f2: out.append((a, b, int(np.median(f1)), int(np.median(f2))))
    return out
if __name__ == '__main__':
    maxf = float(sys.argv[1])
    for p in sys.argv[2:]:
        print(p.split('/')[-1]); [print(f'   {a:.2f}-{b:.2f} ({b-a:.2f}s) F1 {f1} F2 {f2}') for a, b, f1, f2 in seg_formants(p, maxf)]
