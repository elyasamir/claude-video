"""Build index.html for the Wenhua live FCPO chart edit.

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
FIX = {"fcpo": "FCPO", "busa": "Bursa", "mind": "Month", "dahlian": "Dalian",
       "februari": "Februari", "januari": "Januari", "2020-2027": "2027", "bmd": "BMD"}
KEY = {"fcpo", "wenhua", "folder", "bmd", "bursa", "malaysia", "derivative", "m", "active", "month",
       "contract", "februari", "januari", "2027", "favorites", "bintang", "watchlist", "dalian", "live"}
GREEN = {"favorites"}
RED = {"remove"}

def words():
    out = []
    for si, s in enumerate(segs):
        ws = [[w["w"].strip(), w["s"], w["e"]] for w in s["words"]]
        i, merged = 0, []
        while i < len(ws):
            w = ws[i]
            nxt = ws[i + 1][0].lower() if i + 1 < len(ws) else ""
            if w[0].rstrip(",.") in ("2020", "2020-") and nxt.startswith("-2027"):
                merged.append(["2027", w[1], ws[i + 1][2]]); i += 2; continue
            merged.append(w); i += 1
        if si == 0 and merged and merged[0][0].lower().startswith("kalau"):
            merged[0][0] = "So"   # audio says "so"; the cut removed the leading "ok"
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
    ("pop", 8.5, 0.45), ("click", 11.15, 0.6), ("swipe", 12.6, 0.4),
    ("pop", 12.5, 0.4), ("click", 18.85, 0.6), ("whoosh", 19.0, 0.35),
    ("pop", 24.7, 0.45), ("ding", 28.6, 0.3),
    ("pop", 32.1, 0.4), ("click", 39.6, 0.6), ("whoosh", 39.8, 0.35),
    ("pop", 39.4, 0.45), ("click", 46.35, 0.6), ("ding", 46.5, 0.4),
    ("pop", 52.35, 0.45), ("click", 53.05, 0.6), ("click", 59.75, 0.6), ("swipe", 60.0, 0.4),
    ("pop", 61.0, 0.4), ("click", 65.1, 0.55),
    ("pop", 67.85, 0.45), ("click", 70.9, 0.55), ("click", 73.7, 0.6), ("swipe", 73.9, 0.45),
    ("pop", 76.4, 0.45), ("ding", 79.1, 0.35), ("pop", 84.2, 0.4),
    ("whoosh", EDIT_END - 0.05, 0.55), ("impact", EDIT_END + 0.15, 0.5), ("ding", EDIT_END + 0.7, 0.4),
]
DUR = {"impact": 1.2, "whoosh": 0.55, "pop": 0.16, "click": 0.06, "swipe": 0.28, "ding": 1.6,
       "riser": 1.4, "ching": 0.9}
sfx_html = []
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
