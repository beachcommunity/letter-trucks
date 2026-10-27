import numpy as np, scipy.io.wavfile as wf, scipy.signal as ss, scipy.linalg as la, sys
def segments(x, sr, thr_db=-38, minsil=0.08):
    n = int(0.01*sr); fr = np.array([np.sqrt(np.mean(x[i:i+n]**2)) for i in range(0, len(x)-n, n)]) + 1e-9
    db = 20*np.log10(fr/fr.max()); on = db > thr_db
    segs, s = [], None
    for i, v in enumerate(on):
        if v and s is None: s = i
        if not v and s is not None:
            segs.append([s, i]); s = None
    if s is not None: segs.append([s, len(on)])
    merged = []
    for a, b in segs:
        if merged and (a - merged[-1][1]) * 0.01 < minsil: merged[-1][1] = b
        else: merged.append([a, b])
    return [(a*0.01, b*0.01) for a, b in merged if (b-a) > 3]
def formants(x, sr):
    x = ss.resample_poly(x, 1, 2); sr //= 2
    x = np.append(x[0], x[1:] - 0.63*x[:-1]) * np.hamming(len(x))
    o = 12; r = np.correlate(x, x, 'full')[len(x)-1:len(x)+o]
    a = np.concatenate([[1], la.solve_toeplitz(r[:o], -r[1:o+1])])
    fr = sorted([(np.angle(z)*sr/(2*np.pi), -0.5*sr/np.pi*np.log(abs(z))) for z in np.roots(a) if np.imag(z) > 0])
    return [round(f) for f, bw in fr if f > 200 and bw < 400][:3]
def lowratio(x, sr):
    f, P = ss.welch(x, sr, nperseg=512); return P[f < 500].sum() / P[(f >= 500) & (f < 4000)].sum()
if __name__ == '__main__':
 for k in sys.argv[1:]:
     sr, x = wf.read(f'ana/{k}.wav'); x = x.astype(float)
     out = []
     for a, b in segments(x, sr):
         m = (a + b) / 2; w = x[int((m-0.02)*sr):int((m+0.02)*sr)]
         seg = x[int(a*sr):int(b*sr)]
         out.append(f'{a:.2f}-{b:.2f} ({b-a:.2f}s) F{formants(w, sr)} low/hi={lowratio(seg, sr):.1f}')
     print(k); [print('   ', o) for o in out]
