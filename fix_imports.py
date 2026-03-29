filename = "src/blockbt/api/routes/results.py"
with open(filename, "r") as f:
    content = f.read()

content = content.replace("\nimport datetime\n", "")
content = "import datetime\n" + content

with open(filename, "w") as f:
    f.write(content)
