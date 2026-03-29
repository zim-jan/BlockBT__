import sys

filename = "src/blockbt/engine/base.py"
with open(filename, "r") as f:
    content = f.read()

# Fix missing dataclass import
if "from dataclasses import dataclass, field" not in content:
    content = "from dataclasses import dataclass, field\n" + content

with open(filename, "w") as f:
    f.write(content)
