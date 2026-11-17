"""Chroma-key the flat green background out of the presenter photo -> transparent PNG."""
import sys, numpy as np
from PIL import Image, ImageFilter
src, dst = sys.argv[1], sys.argv[2]
im = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
r, g, b = im[..., 0], im[..., 1], im[..., 2]
# "greenness": how much green exceeds the larger of red/blue
gx = g - np.maximum(r, b)
# fully key above 70, fully keep below 25, soft ramp between
alpha = np.clip((70 - gx) / 45, 0, 1)
# clean speckles, then feather the edge slightly
a = Image.fromarray((alpha * 255).astype(np.uint8))
a = a.filter(ImageFilter.MedianFilter(5)).filter(ImageFilter.GaussianBlur(1.2))
alpha = np.asarray(a).astype(np.float32) / 255
# spill suppression: pull green down to max(r,b) where it dominates
spill = np.clip(g - np.maximum(r, b), 0, None)
g2 = g - spill * 0.85
out = np.dstack([r, g2, b, alpha * 255]).clip(0, 255).astype(np.uint8)
img = Image.fromarray(out, "RGBA")
img = img.crop(img.getbbox())
img.save(dst, optimize=True)
print(img.size)
