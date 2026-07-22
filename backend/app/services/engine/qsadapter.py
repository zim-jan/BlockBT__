"""
QSAdapter — Faza 13: generowanie tearsheetów analitycznych (Analytics/Tearsheets).

Adapter buduje samodzielny raport HTML (tearsheet) na podstawie metryk portfela
zwracanych przez ``pf.stats()``. Świadomie NIE korzystamy z ``qs.reports.html()``,
ponieważ ta funkcja:

- zwraca ``None`` (pisze wynik do pliku, a nie do stringa),
- wymaga pełnej serii zwrotów (``returns``), której mock/portfel nie musi udostępniać,
- wymaga backendu graficznego (display) do renderowania wykresów.

Zamiast tego składamy minimalny, air-gapped HTML z tabelą metryk — bez zewnętrznych
zasobów (CDN, czcionki, obrazy), zgodnie z filozofią Self-Hosted / Air-Gapped BlockBT.

Pełny raport QuantStats z wykresami (``qs.reports.html``) jest świadomie odłożonym
rozszerzeniem poza MVP Fazy 13 — patrz ADR-0004.
"""


import html
from datetime import UTC, datetime
from typing import Any

import pandas as pd
from loguru import logger


class QSAdapterService:
    """Serwis budujący tearsheety HTML z metryk portfela (QuantStats-friendly)."""

    @staticmethod
    def _normalize_stats(pf: Any) -> dict[str, Any]:
        """
        Normalizuje wynik ``pf.stats()`` do płaskiego słownika ``{nazwa: wartość}``.

        Obsługuje zarówno ``pandas.Series`` (typowe dla vectorbt/QuantStats), jak
        i zwykły ``dict`` (mock/testy). Przy dowolnym błędzie loguje ostrzeżenie
        i zwraca pusty słownik (wzorzec z ``_extract_qs_metrics``).
        """
        try:
            raw = pf.stats()
        except Exception as e:  # noqa: BLE001 - stats() bywa kruchy na ubogich portfelach
            logger.warning("QSAdapter: pf.stats() zawiodło: {}", e)
            return {}

        if isinstance(raw, pd.Series):
            return {str(k): v for k, v in raw.to_dict().items()}
        if isinstance(raw, dict):
            return {str(k): v for k, v in raw.items()}

        logger.warning("QSAdapter: nieobsługiwany typ stats(): {}", type(raw))
        return {}

    @staticmethod
    def _format_value(value: Any) -> str:
        """Formatuje wartość metryki do czytelnej postaci tekstowej (bezpiecznej dla HTML)."""
        if isinstance(value, float):
            text = f"{value:.4f}"
        elif value is None:
            text = "—"
        else:
            text = str(value)
        return html.escape(text)

    @staticmethod
    def generate_tearsheet(pf: Any, generated_at: datetime | None = None) -> str:
        """
        Buduje samodzielny raport HTML (tearsheet) z metryk ``pf.stats()``.

        Args:
            pf: obiekt portfela udostępniający metodę ``stats()`` zwracającą
                ``pandas.Series`` lub ``dict`` metryk.
            generated_at: znacznik czasu wygenerowania raportu (UTC). Jeśli nie
                podano, używany jest ``datetime.now(UTC)``. Parametr istnieje,
                aby wywołujący (np. endpoint) mógł podać jedno, wspólne źródło
                czasu zamiast duplikować je osobno w HTML i w odpowiedzi API.

        Returns:
            Kompletny dokument HTML (``str``) zawierający tabelę metryk. Air-gapped:
            bez odwołań do zasobów zewnętrznych.
        """
        metrics = QSAdapterService._normalize_stats(pf)
        timestamp = (generated_at or datetime.now(UTC)).isoformat()

        if metrics:
            rows = "\n".join(
                "        <tr>"
                f"<td class=\"metric-name\">{html.escape(str(name))}</td>"
                f"<td class=\"metric-value\">{QSAdapterService._format_value(value)}</td>"
                "</tr>"
                for name, value in metrics.items()
            )
            table = (
                "    <table class=\"metrics\">\n"
                "      <thead><tr><th>Metryka</th><th>Wartość</th></tr></thead>\n"
                "      <tbody>\n"
                f"{rows}\n"
                "      </tbody>\n"
                "    </table>"
            )
        else:
            table = "    <p class=\"empty\">Brak dostępnych metryk dla tego portfela.</p>"

        return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="language" content="pl">
  <title>BlockBT — Tearsheet</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #1f2937; }}
    h1 {{ font-size: 1.5rem; }}
    .generated {{ color: #6b7280; font-size: 0.85rem; margin-bottom: 1.5rem; }}
    table.metrics {{ border-collapse: collapse; width: 100%; max-width: 640px; }}
    table.metrics th, table.metrics td {{
      border: 1px solid #e5e7eb; padding: 0.5rem 0.75rem; text-align: left;
    }}
    table.metrics th {{ background: #f3f4f6; }}
    td.metric-value {{ font-variant-numeric: tabular-nums; text-align: right; }}
    p.empty {{ color: #9ca3af; font-style: italic; }}
  </style>
</head>
<body>
  <h1>BlockBT — Tearsheet analityczny</h1>
  <p class="generated">Wygenerowano (UTC): {html.escape(timestamp)}</p>
{table}
</body>
</html>"""
