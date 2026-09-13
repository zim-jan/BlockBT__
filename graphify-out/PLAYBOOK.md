# graphify — regeneracja grafu wiedzy BlockBT

Graf w tym katalogu powstaje narzędziem [graphify](https://github.com/Graphify-Labs/graphify)
(pakiet PyPI `graphifyy`). Jest mapą do nawigacji po kodzie i dokumentacji — rozstrzyga
kod, nie graf.

## Pełna przebudowa

Z poziomu agenta, który ma zainstalowany skill graphify (np. Claude Code), w korzeniu repo:

```
/graphify .
```

Kod jest ekstrahowany strukturalnie (AST, bez modelu językowego). Dokumenty (`*.md`,
`*.yml`, `*.html`) przechodzą ekstrakcję semantyczną wykonywaną przez samego agenta albo
przez Gemini, jeśli ustawiono `GEMINI_API_KEY`. Pełny przebieg kosztuje tokeny —
skumulowany koszt zapisuje `cost.json`.

## Aktualizacja po zmianach w kodzie

```
graphify update .
```

Przelicza wyłącznie pliki kodu (AST), bez modelu językowego i bez kosztu. Zmiany
w dokumentacji wymagają pełnej przebudowy.

## Co jest wykluczane

| Cel | Mechanizm | Powód |
|:--|:--|:--|
| `site/` (build MkDocs) | `.graphifyignore` w korzeniu repo | 1:1 duplikat `docs/*.md` plus zvendorowany JS mkdocs-material i Lunr.js — zero unikalnej informacji |
| `.env*` | wbudowany filtr plików wrażliwych | graphify pomija je przy detekcji |

Nowy katalog z wygenerowanym outputem, którego źródło już jest w grafie, dopisz do
`.graphifyignore`.

## Wyjścia

| Plik | Zawartość | W repo |
|:--|:--|:--|
| `GRAPH_REPORT.md` | raport: węzły centralne, społeczności, nieoczywiste powiązania, sugerowane pytania | tak |
| `graph.html` | interaktywna wizualizacja — otwórz w przeglądarce | tak |
| `graph.json` | surowe dane grafu (node-link, gotowe pod GraphRAG) | tak |
| `manifest.json` | stan plików dla `graphify update` | tak |
| `.graphify_labels.json` | nazwy społeczności używane przez wizualizację | tak |
| `cost.json` | skumulowany koszt tokenów | tak |
| `cache/` | cache ekstrakcji AST i semantycznej | nie (`.gitignore`) |

Cache nie jest wersjonowany, więc pierwsza przebudowa w świeżym klonie przelicza
wszystko od zera.

## Odpytywanie

```
graphify query "jak przepływa DAG strategii od edytora do silnika?"
graphify path "GraphParser" "IndicatorService"
graphify explain "OpenSourceEngine"
graphify god-nodes
```

Wszystkie komendy działają na istniejącym `graph.json`, bez przebudowy.
