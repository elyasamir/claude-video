"""Build index.html for the TradingView spread-chart edit.

Inputs (all in assets/):
  cuts.json   kept ranges of the raw recording, in source seconds
  words.json  whisper word timings of the cut audio (output timeline)
Run: python3 -I tools/build.py   (from the project folder)
"""
import json, html, os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cuts = json.load(open(os.path.join(HERE, "assets/cuts.json")))
segs = json.load(open(os.path.join(HERE, "assets/words.json")))
EDIT_END = round(sum(e - s for s, e in cuts), 2)          # end of the talking edit
OUTRO = 4.8
TOTAL = round(EDIT_END + OUTRO, 2)

# ---------------------------------------------------------------- captions
FIX = {"fcpo": "FCPO", "simbol": "symbol", "kontrak": "contract", "aktif": "active",
       "februari": "February", "yaitu": "iaitu", "qst": "QST"}
KEY = {"spread", "tradingview", "watchlist", "fcpo", "g2027", "h2027", "gh", "line", "heikin ashi",
       "candlestick", "support", "resistance", "2-3", "tick", "manual", "qst", "february", "enter",
       "symbol", "noise", "trend", "futures"}
GREEN = {"support"}
RED = {"resistance", "noise"}

def words():
    out = []
    for si, s in enumerate(segs):
        ws = [[w["w"].strip(), w["s"], w["e"]] for w in s["words"]]
        # the speaker said "FCPO GH" here; whisper heard G2027
        if 52 < s["start"] < 53.5 and ws[-1][0].upper() == "G2027":
            ws[-1][0] = "GH"
        i, merged = 0, []
        while i < len(ws):
            w = ws[i]
            nxt = ws[i + 1][0].lower() if i + 1 < len(ws) else ""
            if w[0].lower() == "trading" and nxt.startswith("view"):
                merged.append(["TradingView", w[1], ws[i + 1][2]]); i += 2; continue
            if w[0].lower() == "heki" and nxt.startswith("nashi"):
                merged.append(["Heikin Ashi", w[1], ws[i + 1][2]]); i += 2; continue
            if w[0] == "2" and nxt == "-3":
                merged.append(["2-3", w[1], ws[i + 1][2]]); i += 2; continue
            merged.append(w); i += 1
        for w in merged:
            w[0] = FIX.get(w[0].lower(), w[0])
            out.append((si, w))
    return out

def chunks():
    ws = words()
    caps, cur, cur_seg = [], [], None
    for si, (t, s, e) in ws:
        if cur and (si != cur_seg or len(cur) >= 5 or len(" ".join(x[0] for x in cur + [[t]])) > 30):
            caps.append(cur); cur = []
        cur.append([t, s, e]); cur_seg = si
    if cur: caps.append(cur)
    # never leave a lone word on its own: fold it into the caption before it (same sentence)
    merged = []
    for c in caps:
        if len(c) == 1 and merged and len(merged[-1]) <= 5 and c[0][1] - merged[-1][-1][2] < 0.6:
            merged[-1] = merged[-1] + c
        else:
            merged.append(c)
    caps = merged
    res = []
    for i, c in enumerate(caps):
        # whisper stretches the first word of a sentence back over the pause before it
        first = max(c[0][1], c[0][2] - 0.45)
        c[0][1] = first
        nxt = caps[i + 1][0][1] if i + 1 < len(caps) else None
        end = c[-1][2] + 0.35
        if nxt is not None:
            nxt_first = max(caps[i + 1][0][1], caps[i + 1][0][2] - 0.45)
            end = min(end, nxt_first - 0.02)
        end = min(end, EDIT_END)
        items = []
        for t, s, e in c:
            k = t.lower().strip(",.")
            cls = "g" if k in GREEN else "r" if k in RED else "k" if k in KEY else ""
            items.append([t, round(max(s, first), 2), cls])
        res.append([items, round(max(end, items[-1][1] + 0.3), 2)])
    return res

CAPS = chunks()

# ---------------------------------------------------------------- clips
clip_html = []
t = 0.0
for i, (s, e) in enumerate(cuts):
    d = round(e - s, 3)
    clip_html.append(
        f'              <video id="v{i}" class="clip" src="assets/raw.mp4" data-start="{round(t, 3)}" '
        f'data-duration="{d}" data-media-start="{s}" data-has-audio="true" data-fade-in="0.02" '
        f'data-fade-out="0.03" data-track-index="1" playsinline></video>')
    t += d
# hold the last frame (muted) under the outro
clip_html.append(
    f'              <video id="vhold" class="clip" src="assets/raw.mp4" data-start="{EDIT_END}" '
    f'data-duration="0.8" data-media-start="{cuts[-1][1]}" muted data-track-index="1" playsinline></video>')

# ---------------------------------------------------------------- sfx
SFX = [  # (file, start, volume)
    ("impact", 0.05, 0.6), ("whoosh", 0.0, 0.5),
    ("pop", 5.7, 0.45),                     # step 1
    ("pop", 15.6, 0.45), ("click", 16.55, 0.6),   # add symbol
    ("swipe", 20.55, 0.4),                  # month codes card
    ("pop", 26.5, 0.45),                    # step 3
    ("pop", 31.1, 0.5), ("pop", 34.2, 0.4), ("pop", 37.1, 0.5),   # code chips
    ("click", 40.46, 0.6), ("whoosh", 40.7, 0.35),
    ("swipe", 43.0, 0.45), ("click", 48.75, 0.6),
    ("whoosh", 49.9, 0.4), ("ding", 52.3, 0.35),
    ("click", 63.71, 0.55), ("swipe", 64.3, 0.4),
    ("click", 71.6, 0.55), ("swipe", 72.0, 0.4),
    ("click", 77.03, 0.55), ("ding", 77.6, 0.3),
    ("click", 80.6, 0.5),
    ("swipe", 85.7, 0.45), ("swipe", 89.8, 0.45),
    ("whoosh", 91.7, 0.5), ("riser", 94.0, 0.35), ("ding", 95.4, 0.35),
    ("pop", 97.6, 0.45), ("ching", 106.1, 0.4), ("pop", 110.8, 0.45), ("pop", 118.0, 0.45),
    ("whoosh", EDIT_END - 0.05, 0.55), ("impact", EDIT_END + 0.15, 0.5), ("ding", EDIT_END + 0.7, 0.4),
]
DUR = {"impact": 1.2, "whoosh": 0.55, "pop": 0.16, "click": 0.06, "swipe": 0.28, "ding": 1.6,
       "riser": 1.4, "ching": 0.9}
sfx_html = [f'      <audio id="music" class="clip" src="assets/sfx/music.m4a" data-start="0" '
            f'data-duration="{TOTAL}" data-volume="0.12" data-fade-in="0.8" data-fade-out="2" data-track-index="2"></audio>']
for i, (f, st, v) in enumerate(SFX):
    sfx_html.append(f'      <audio id="sfx{i}" src="assets/sfx/{f}.wav" data-start="{st}" data-duration="{DUR[f]}" '
                    f'data-volume="{v}" data-track-index="{3 + i % 3}"></audio>')

tpl = open(os.path.join(HERE, "tools/template.html")).read()
out = (tpl.replace("{{TOTAL}}", str(TOTAL))
          .replace("{{EDIT_END}}", str(EDIT_END))
          .replace("{{CLIPS}}", "\n".join(clip_html))
          .replace("{{SFX}}", "\n".join(sfx_html))
          .replace("{{CAPS}}", json.dumps(CAPS, ensure_ascii=False)))
open(os.path.join(HERE, "index.html"), "w").write(out)
print("edit", EDIT_END, "total", TOTAL, "captions", len(CAPS), "clips", len(cuts))
