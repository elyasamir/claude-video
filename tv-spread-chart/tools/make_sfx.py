"""Synthesise the film's sound effects and music bed (deterministic, no downloads)."""
import numpy as np, wave, os, sys
SR = 44100
out = sys.argv[1]
rng = np.random.default_rng(7)

def save(name, x, peak=0.89):
    x = np.asarray(x, np.float64)
    if x.ndim == 1: x = np.stack([x, x], 1)
    x = x / (np.abs(x).max() + 1e-9) * peak
    with wave.open(os.path.join(out, name), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())

def t(d): return np.arange(int(SR * d)) / SR

def lp(x, a):  # one-pole lowpass, a in (0,1) per-sample or array
    y = np.zeros_like(x); s = 0.0
    a = np.broadcast_to(a, x.shape)
    for i in range(len(x)): s += a[i] * (x[i] - s); y[i] = s
    return y

def env(n, att, dec_curve=3.0):
    e = np.ones(n); na = max(1, int(att * SR)); e[:na] = np.linspace(0, 1, na)
    e[na:] = (1 - np.linspace(0, 1, n - na)) ** dec_curve
    return e

# whoosh: noise through a sweeping lowpass, swelling then fading
d = 0.55; n = int(SR * d); tt = t(d)
sweep = 0.02 + 0.35 * np.sin(np.pi * tt / d) ** 2
nz = rng.standard_normal(n)
w = lp(nz, sweep) - lp(nz, sweep * 0.15)
shape = np.sin(np.pi * np.clip(tt / d, 0, 1)) ** 1.5
L = w * shape; R = np.roll(w, 220) * shape
pan = np.linspace(0.3, 1.0, n)
save("whoosh.wav", np.stack([L * (1.3 - pan), R * pan], 1), 0.8)

# pop: quick pitched bubble
d = 0.16; tt = t(d)
f = 900 * np.exp(-tt * 18) + 380
ph = 2 * np.pi * np.cumsum(f) / SR
save("pop.wav", np.sin(ph) * env(len(tt), 0.002, 4), 0.75)

# click / tap
d = 0.06; tt = t(d)
c = (np.sin(2 * np.pi * 2400 * tt) * 0.6 + rng.standard_normal(len(tt)) * 0.4) * np.exp(-tt * 140)
save("click.wav", c, 0.7)

# ding: bell partials
d = 1.6; tt = t(d)
b = sum(a * np.sin(2 * np.pi * f0 * tt) * np.exp(-tt * k) for f0, a, k in
        [(1318.5, 1.0, 3.0), (2637, 0.35, 5), (3950, 0.15, 8), (1975.5, 0.25, 4)])
b *= np.minimum(1, tt / 0.003)
save("ding.wav", b, 0.7)

# impact: sub drop + noise burst (intro slam)
d = 1.2; tt = t(d)
f = 110 * np.exp(-tt * 6) + 42
sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 3.2)
burst = lp(rng.standard_normal(len(tt)), 0.25) * np.exp(-tt * 22)
save("impact.wav", sub + burst * 0.6, 0.9)

# riser: rising filtered noise + tone, 1.4s
d = 1.4; n = int(SR * d); tt = t(d)
nz = lp(rng.standard_normal(n), 0.02 + 0.4 * (tt / d) ** 2)
tone = np.sin(2 * np.pi * np.cumsum(200 + 900 * (tt / d) ** 2) / SR) * 0.25
save("riser.wav", (nz + tone) * (tt / d) ** 2, 0.7)

# swipe: short bright swish for highlights
d = 0.28; n = int(SR * d); tt = t(d)
nz = rng.standard_normal(n)
s = (nz - lp(nz, 0.3)) * np.sin(np.pi * tt / d) ** 2
save("swipe.wav", s, 0.6)

# cash-register style "cha-ching" for the spread maths
d = 0.9; tt = t(d)
def bell(f0, st):
    x = np.zeros_like(tt); m = tt >= st; u = tt[m] - st
    x[m] = (np.sin(2*np.pi*f0*u) + 0.4*np.sin(2*np.pi*f0*2.76*u)) * np.exp(-u * 7)
    return x
save("ching.wav", bell(2093, 0) * 0.7 + bell(2637, 0.09) + 0.3 * np.exp(-tt*60) * rng.standard_normal(len(tt)), 0.65)

# music bed: soft lo-fi loop, 84 bpm, Fmaj7 - Em7 - Dm7 - Cmaj7, 34s
bpm = 84; beat = 60 / bpm; dur = float(os.environ.get("MUSIC_DUR", "34")); N = int(SR * dur); tt = t(dur)
mix = np.zeros((N, 2))
def midi(m): return 440 * 2 ** ((m - 69) / 12)
chords = [[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [48, 52, 55, 59]]
bar = beat * 4
for k in range(int(dur / bar) + 1):
    ch = chords[k % 4]; st = k * bar
    i0 = int(st * SR); i1 = min(N, int((st + bar) * SR))
    if i0 >= N: break
    u = tt[i0:i1] - st
    e = np.minimum(1, u / 0.25) * np.minimum(1, (bar - u) / 0.3)
    pad = sum(np.sin(2*np.pi*midi(m)*u + 0.3*np.sin(2*np.pi*0.3*u)) for m in ch) / len(ch)
    mix[i0:i1, 0] += pad * e * 0.35; mix[i0:i1, 1] += pad * e * 0.35
    # bass root
    bu = np.sin(2*np.pi*midi(ch[0]-12)*u) * np.exp(-u*1.2)
    mix[i0:i1] += (bu * 0.45)[:, None]
# pad smoothing
for c in range(2): mix[:, c] = lp(mix[:, c], 0.08)
# drums
for b in range(int(dur / beat)):
    st = b * beat; i0 = int(st * SR)
    if b % 4 in (0, 2) or b % 8 == 7:
        u = t(0.35); kk = np.sin(2*np.pi*np.cumsum(50 + 90*np.exp(-u*30))/SR) * np.exp(-u*9)
        j = min(N, i0 + len(u)); mix[i0:j] += (kk[:j-i0] * 0.8)[:, None]
    if b % 4 in (1, 3):
        u = t(0.2); sn = lp(rng.standard_normal(len(u)), 0.35) * np.exp(-u*20) * 0.35
        j = min(N, i0 + len(u)); mix[i0:j] += sn[:j-i0, None]
    for h in (0, 0.5):
        hi = int((st + h * beat) * SR); u = t(0.05)
        hh = rng.standard_normal(len(u)); hh = (hh - lp(hh, 0.5)) * np.exp(-u*90) * (0.18 if h else 0.1)
        j = min(N, hi + len(u)); mix[hi:j, 0] += hh[:j-hi] * 0.8; mix[hi:j, 1] += hh[:j-hi]
fade = np.minimum(1, tt / 1.0) * np.minimum(1, (dur - tt) / 2.0)
save("music.wav", mix * fade[:, None], 0.8)
print("ok")
