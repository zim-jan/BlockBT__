
filename = "src/blockbt/engine/base.py"
with open(filename) as f:
    content = f.read()

content = content.replace("from dataclasses import dataclass, field\n", "")
content = content.replace("from __future__ import annotations\n", "from __future__ import annotations\nfrom dataclasses import dataclass, field\n")

with open(filename, "w") as f:
    f.write(content)
