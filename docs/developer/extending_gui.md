# Przewodnik: Rozszerzanie UI (Strony i Węzły)

BlockBT używa minimalistycznego, ale potężnego stacku Streamlit. Dzięki aplikacjom wielostronicowym (`Multipage App`), dodawanie nowych widoków jest trywialne.

## 📄 Dodawanie Nowej Strony

1. **Stwórz plik w folderze `/pages/`**:
   Np. `7_Performance_Deep_Dive.py`. Streamlit automatycznie wykryje nowy plik i doda go do menu bocznego (nazwa pliku bez numerka stanie się etykietą).
   
2. **Dodaj Bramkę Autoryzacji**:
   Każda nowa strona powinna zaczynać się od sprawdzenia sesji, aby nieuprawnieni użytkownicy nie widzieli danych.

```python
import streamlit as st
from blockbt.ui.auth import is_logged_in, render_auth_gate

if not is_logged_in():
    render_auth_gate()

# Twoja logika GUI...
st.title("Nowa Analiza")
```

## 🔀 Rozszerzanie Visual Buildera (Węzły)

Edytor graficzny w `6_Visual_Builder.py` bazuje na bibliotece `streamlit-flow-component`. 

### Jak dodać nowy typ węzła do płótna?
Węzły definiujemy jako listę obiektów `StreamlitFlowNode`. 

```python
# Przykład dodania węzła oscylatora RSI:
new_node = StreamlitFlowNode(
    id="rsi_node", 
    pos=(500, 300), 
    data={"content": "Wskaźnik: RSI (14)"}, 
    node_type="default", 
    source_position="right", 
    target_position="left"
)
```

### Mapowanie Węzła na Silnik (AST)
Kiedy użytkownik połączy węzły, system generuje JSON. Aby silnik wiedział co z tym zrobić, musisz zaktualizować parser w `src/blockbt/engine/opensource_engine.py`.

1. Przejdź do metody zajmującej się `visual_ast`.
2. Dodaj logikę rozpoznawania ID węzła i wywoływania odpowiedniej funkcji z `pandas-ta`.

## 🎨 Design System

Mimo że Streamlit ma własne style, trzymamy się kilku zasad:
- **`st.divider()`**: Oddzielaj sekcje konfiguracji od wyników.
- **`st.columns()`**: Używaj do tworzenia metryk "Headline" (PnL, Sharpe, etc.).
- **Plotly**: Wszystkie wykresy (equity curve, histogramy) powinny być interaktywne.

---
### Zobacz też:
- [Visual Builder Source](file:///home/przydan/my_project/pages/6_Visual_Builder.py) — główne źródło logiki grafowej.
- [Dashboard Source](file:///home/przydan/my_project/pages/2_Dashboard.py) — wzorzec dla stron analitycznych.
