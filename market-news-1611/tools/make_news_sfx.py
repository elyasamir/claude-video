"""News-style stings, synthesised (deterministic, no downloads)."""
import numpy as np, wave, os, sys
SR = 44100; out = sys.argv[1]; rng = np.random.default_rng(3)
def save(name, x, peak=0.9):
    x = np.asarray(x, float)
    if x.ndim == 1: x = np.stack([x, x], 1)
    x = x / (np.abs(x).max() + 1e-9) * peak
    with wave.open(os.path.join(out, name), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype(np.int16).tobytes())
def t(d): return np.arange(int(SR * d)) / SR
def midi(m): return 440 * 2 ** ((m - 69) / 12)
def brass(f, d, att=0.02):
    tt = t(d); x = sum(np.sin(2*np.pi*f*k*tt) / k**1.1 for k in range(1, 9))
    return x * np.minimum(1, tt/att) * np.exp(-tt*2.2)
def timp(f, d):
    tt = t(d); return np.sin(2*np.pi*f*tt*(1+0.08*np.exp(-tt*8))) * np.exp(-tt*4) + 0.3*rng.standard_normal(len(tt))*np.exp(-tt*25)
# sting: rising roll + two stabs
d = 2.6; N = int(SR*d); x = np.zeros(N)
roll = rng.standard_normal(int(SR*0.7)) * np.linspace(0, 1, int(SR*0.7))**2 * 0.25
x[:len(roll)] += np.convolve(roll, np.ones(30)/30, 'same')
for st, ch in [(0.7, [55, 62, 67, 71]), (1.05, [57, 64, 69, 72])]:
    a = int(st*SR); s = sum(brass(midi(m), d-st) for m in ch) / 4 + timp(midi(ch[0]-24), d-st)*0.8
    n = min(N - a, len(s)); x[a:a+n] += s[:n]
save("sting.wav", x)
# blip: two-tone news transition
tt = t(0.32); b = np.where(tt < 0.12, np.sin(2*np.pi*1320*tt), np.sin(2*np.pi*1760*tt)) * np.exp(-((tt % 0.16))*14) * np.minimum(1, tt/0.004)
save("blip.wav", b, 0.6)
# low hit for section changes
tt = t(0.9); save("hit.wav", timp(55, 0.9) + 0.4*sum(brass(midi(m), 0.9) for m in [43, 50]) , 0.85)
print("ok")
