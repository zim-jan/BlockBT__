"""Django management script dla BlockBT."""

import os
import sys


def main() -> None:
    """Uruchom komendy administracyjne Django."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "blockbt.settings")
    try:
        from django.core.management import execute_from_command_line  # noqa: PLC0415
    except ImportError as exc:
        msg = (
            "Nie mozna zaimportowac Django. Upewnij sie, ze Django jest "
            "zainstalowane i dostepne w zmiennej PYTHONPATH. "
            "Czy aktywowales srodowisko wirtualne?"
        )
        raise ImportError(msg) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
