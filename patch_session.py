import re
with open("backend/app/db/session.py", "r") as f:
    content = f.read()

content += """
def drop_db() -> None:
    \"\"\"Drop all Phase 2 tables.\"\"\"
    Base.metadata.drop_all(bind=_engine)
"""

# Update the fallback path calculation since the file moved from src/blockbt/models/session.py to backend/app/db/session.py
content = re.sub(
    r'fallback = Path\(__file__\).resolve\(\).parents\[3\] / "local_data" / "db" / "blockbt.db"',
    r'fallback = Path(__file__).resolve().parents[3] / "local_data" / "db" / "blockbt.db"',
    content
)

with open("backend/app/db/session.py", "w") as f:
    f.write(content)
