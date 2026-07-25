# Polityka bezpieczeństwa

## Zgłaszanie podatności

**Nie zgłaszaj podatności przez publiczne issue.**

Użyj zakładki **Security → Report a vulnerability** (GitHub Private Vulnerability
Reporting) w tym repozytorium. Jeśli funkcja jest niedostępna, otwórz issue
zatytułowane „Security contact request" bez żadnych szczegółów technicznych,
a odezwiemy się kanałem prywatnym.

W zgłoszeniu przydatne są: wersja lub commit, kroki odtworzenia, wpływ oraz —
jeśli masz — proponowana poprawka.

Odpowiadamy w miarę możliwości; to projekt prowadzony po godzinach, bez SLA.

## Zakres

BlockBT jest przeznaczony do uruchamiania **lokalnie, przez jednego użytkownika**,
z nasłuchem na `127.0.0.1`. Dwa obszary zasługują na szczególną uwagę:

### Piaskownica wskaźników użytkownika

Aplikacja pozwala wpisać własny wskaźnik w Pythonie i go wykonać. Kod przechodzi
przez walidator AST (`backend/app/services/engine/indicators.py`) z listą dozwolonych
węzłów oraz czarną listą nazw (`eval`, `exec`, `__import__`, `os`, `subprocess`,
dostęp do atrybutów `f_globals`, `gi_frame` itd.).

**Ta piaskownica jest zabezpieczeniem przed pomyłką, nie przed atakiem.** Ucieczki
z piaskownic opartych o AST w CPythonie są znanym problemem klasy badawczej.
Nie wystawiaj BlockBT na niezaufanych użytkowników i nie uruchamiaj cudzych
wskaźników bez przeczytania ich. Obejścia walidatora **przyjmujemy jako zgłoszenia
bezpieczeństwa** i traktujemy poważnie.

### Uwierzytelnianie i granica zaufania

Uwierzytelnianie JWT jest opcjonalne i domyślnie wyłączone (`AppSetting` w bazie).
Model zagrożeń opiera się na założeniu, że **granicą zaufania jest loopback** —
uzasadnienie w `docs/adr/0011-loopback-jako-granica-zaufania.md`.

Jeśli wystawisz instancję poza `127.0.0.1`, wychodzisz poza zakładany model
zagrożeń i robisz to na własną odpowiedzialność. Zgłoszenia sprowadzające się do
„wystawiłem to na 0.0.0.0 bez auth i ktoś wszedł" nie są traktowane jako podatność.

## Poza zakresem

- Ataki wymagające lokalnego dostępu do konta użytkownika, na którym działa aplikacja.
- Podatności w zależnościach zewnętrznych — zgłaszaj je do właściwych projektów
  (raporty o nieaktualnej wersji zależności w `uv.lock` są jednak mile widziane).
- Konfiguracje jawnie odradzane w dokumentacji.

## Sekrety

`SECRET_KEY` służy do szyfrowania Fernet i **nie ma wartości domyślnej** — aplikacja
nie wstanie bez niego. Nie commituj `.env`; `.env.example` zawiera wyłącznie
placeholdery i komendę generującą klucz.
