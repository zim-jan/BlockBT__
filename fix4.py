import re

with open("src/blockbt/api/routes/results.py", "r") as f:
    content = f.read()

content = content.replace("from pydantic import BaseModel", "")

lines = content.split("\n")
for i, line in enumerate(lines):
    if line.startswith("import pandas as pd"):
        lines.insert(i + 1, "from pydantic import BaseModel")
        break

with open("src/blockbt/api/routes/results.py", "w") as f:
    f.write("\n".join(lines))
