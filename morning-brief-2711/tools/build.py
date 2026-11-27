"""Assemble index.html = tools/body.html with tools/base.css + tools/extra.css inlined."""
import os
H = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
r = lambda p: open(os.path.join(H, p)).read()
open(os.path.join(H, "index.html"), "w").write(r("tools/body.html").replace("{{STYLE}}", r("tools/base.css") + "\n" + r("tools/extra.css")))
print("ok")
