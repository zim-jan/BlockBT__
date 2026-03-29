
filename = "src/blockbt/models/orm.py"
with open(filename) as f:
    content = f.read()

# Szukamy klasy BacktestJob i dodajemy nową relację
search_job = '    strategy: Mapped[Strategy] = relationship("Strategy", back_populates="backtest_jobs")'
replace_job = '''    strategy: Mapped[Strategy] = relationship("Strategy", back_populates="backtest_jobs")
    chat_messages: Mapped[list["ChatMessage"]] = relationship("ChatMessage", back_populates="job", cascade="all, delete-orphan")'''
content = content.replace(search_job, replace_job)

# Dodajemy nową klasę ChatMessage na końcu pliku
new_class = '''

class ChatMessage(Base):
    """Model reprezentujący pojedynczą wiadomość czatu dla zadania backtestu.

    Służy do przechowywania historii konwersacji między użytkownikiem a asystentem AI
    (LLM) po wygenerowaniu początkowego raportu analizy.
    """

    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("backtest_jobs.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, default=_utcnow
    )

    job: Mapped[BacktestJob] = relationship("BacktestJob", back_populates="chat_messages")

    def __repr__(self) -> str:
        return f"<ChatMessage id={self.id} job_id={self.job_id} role={self.role!r}>"
'''
content += new_class

with open(filename, "w") as f:
    f.write(content)

print("Patched orm.py successfully.")
