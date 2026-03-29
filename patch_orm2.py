import sys

filename = "src/blockbt/models/orm.py"
with open(filename, "r") as f:
    content = f.read()

# Fix line lengths
content = content.replace(
    'chat_messages: Mapped[list[ChatMessage]] = relationship("ChatMessage", back_populates="job", cascade="all, delete-orphan")',
    'chat_messages: Mapped[list[ChatMessage]] = relationship(\n        "ChatMessage", back_populates="job", cascade="all, delete-orphan"\n    )'
)

content = content.replace(
    'job_id: Mapped[int] = mapped_column(ForeignKey("backtest_jobs.id", ondelete="CASCADE"), nullable=False)',
    'job_id: Mapped[int] = mapped_column(\n        ForeignKey("backtest_jobs.id", ondelete="CASCADE"), nullable=False\n    )'
)

with open(filename, "w") as f:
    f.write(content)

print("Patched orm.py successfully.")
