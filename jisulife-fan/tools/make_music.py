"""Soft, minimal music bed: plucked arpeggios over a warm pad (deterministic, no downloads)."""
import numpy as np, wave, sys
SR = 44100; dur = float(sys.argv[2]) if len(sys.argv) > 2 else 30.0
N = int(SR * dur); mix = np.zeros((N, 2))
def midi(m): return 440 * 2 ** ((m - 69) / 12)
def pluck(f, d, seed):
    n = int(SR * d); p = max(2, int(SR / f)); rng = np.random.default_rng(seed)
    buf = rng.uniform(-1, 1, p); out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % p]
        buf[i % p] = 0.5 * (buf[i % p] + buf[(i + 1) % p]) * 0.996
    return out * np.minimum(1, np.arange(n) / 80)
bpm = 88; beat = 60 / bpm; bar = 4 * beat
chords = [[60, 64, 67, 71], [57, 60, 64, 67], [53, 57, 60, 64], [55, 59, 62, 67]]   # Cmaj7 Am7 Fmaj7 G
pattern = [0, 2, 1, 3, 2, 1, 3, 2]
seed = 1
for k in range(int(dur / bar) + 1):
    ch = chords[k % 4]; st = k * bar
    # pad
    i0 = int(st * SR); i1 = min(N, int((st + bar) * SR))
    if i0 >= N: break
    u = np.arange(i1 - i0) / SR
    e = np.minimum(1, u / 0.6) * np.minimum(1, (bar - u) / 0.6)
    pad = sum(np.sin(2*np.pi*midi(m-12)*u) for m in ch[:3]) / 3
    mix[i0:i1] += (pad * e * 0.18)[:, None]
    # arpeggio, 8ths
    for j, idx in enumerate(pattern):
        t0 = st + j * beat / 2; a = int(t0 * SR)
        if a >= N: break
        note = ch[idx] + (12 if j in (3, 6) else 0)
        x = pluck(midi(note), 1.6, seed); seed += 1
        b = min(N, a + len(x)); pan = 0.35 + 0.3 * (j % 2)
        mix[a:b, 0] += x[:b-a] * 0.32 * (1 - pan); mix[a:b, 1] += x[:b-a] * 0.32 * pan
    # soft low note
    x = np.sin(2*np.pi*midi(ch[0]-24)*np.arange(int(bar*SR))/SR) * np.exp(-np.arange(int(bar*SR))/SR*1.5)
    b = min(N, i0 + len(x)); mix[i0:b] += (x[:b-i0] * 0.25)[:, None]
tt = np.arange(N) / SR
mix *= (np.minimum(1, tt / 1.5) * np.minimum(1, (dur - tt) / 2.5))[:, None]
mix = mix / np.abs(mix).max() * 0.85
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("ok")
