# Przewodnik: Baza Danych i Migracje (SQLAlchemy + Alembic)

BlockBT korzysta z bazy danych SQLite oraz ORM SQLAlchemy 2.x do przechowywania trwałych danych.

## 🏗️ Rozszerzanie Modeli

Wszystkie tabele są zdefiniowane w pliku `backend/app/models/orm.py`.

### Jak dodać nową kolumnę?
1. Otwórz `models.py`.
2. Dodaj atrybut z adnotacją `Mapped` i funkcją `mapped_column`.

```python
class StrategyTemplate(Base):
    # ... istniejące pola ...
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
```

## 🔄 Migracje (Alembic)

Używamy Alembic, aby aktualizować strukturę bazy u użytkowników bez usuwania ich dotychczasowych danych.

### 1. Wygeneruj skrypt migracji
Gdy zmienisz coś w `models.py`, uruchom w terminalu:
```bash
alembic revision --autogenerate -m "Add is_public to StrategyTemplate"
```

### 2. Sprawdź wygenerowany kod
Daj okiem do folderu `alembic/versions/`. Upewnij się, że operacje `upgrade` i `downgrade` wyglądają poprawnie.

### 3. Zastosuj zmiany
```bash
alembic upgrade head
```

## 🔌 Używanie Sesji w Kodzie

Zawsze używaj context managera `get_session()` z pliku `backend/app/db/session.py`, aby uniknąć błędów wycieku połączeń.

```python
from blockbt.db.session import get_session
from blockbt.db.models import User

with get_session() as db:
    user = db.query(User).filter_by(id=1).first()
    # sesja zamknie się automatycznie po wyjściu z bloku 'with'
```

---
### Uwaga:
- Wersja SQLite używana lokalnie to plik `blockbt.db` (często ignorowany w GIT).
- Pamiętaj o typach JSON — przechowujemy w nich duże słowniki stanów Wizardów i metryk silnika.
