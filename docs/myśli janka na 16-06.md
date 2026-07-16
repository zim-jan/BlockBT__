### USECASE 1 
## 1 symbol
- Wybór DataSource (Yahoo)
- Wybór symbolu (APPL)
- Wybór wskaźnika (Boolinger Bands)
|Nazwa Parametru|Wartość parametru|
----------------------------------
|Length_1|100|
|Length_2|200|
- Ze wskaźnika BB wychodzą 3 wartości, wybór niższej, średniej i wyższej (potrzebna funkcjonalność, która w przypadku wybrania odpowiednich wskaźników, będzie modyfikowała node ze wskaźnikiem, e.g. w przypadku BB, dodatkowy DropDown menu do wyboru bb_low, bb_mid i bb_high)
- Wybór warunku do sygnału, jeżeli jest poniżej średniej i ją przekroczy, trzymać dopóki nie spadnie poniżej

### USECASE 2
## 1 symbol + optymalizacja
- Wybór DataSource (Yahoo)
- Wybór symbolu (APPL)
- Wybór wskaźnika (Boolinger Bands)
|Nazwa Parametru|Wartość parametru|
----------------------------------
|Length_1|Optuna_X|
|Length_2|Optuna_Y|
- Ze wskaźnika BB wychodzą 3 wartości, wybór niższej, średniej i wyższej
- Wybór warunku do sygnału, jeżeli jest poniżej średniej i ją przekroczy, trzymać dopóki nie spadnie poniżej
- 
