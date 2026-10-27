import numpy as np, scipy.io.wavfile as wf, sys
sys.path.insert(0, 'ana'); from seg import segments, formants
for k in sys.argv[1:]:
    sr, x = wf.read(f'ana/{k}.wav'); x = x.astype(float)
    print(k)
    for a, b in segments(x, sr, thr_db=-35, minsil=0.06):
        fs = []
        for m in np.linspace(a + (b-a)*0.25, a + (b-a)*0.75, 7):
            F = formants(x[int((m-0.0125)*sr):int((m+0.0125)*sr)], sr)
            if len(F) >= 2: fs.append(F[:2])
        med = np.median(np.array(fs), axis=0).astype(int).tolist() if fs else None
        print(f'   {a:.2f}-{b:.2f} ({b-a:.2f}s) median F1/F2 {med}')
