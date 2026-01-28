"""Wspoldzielone fixtures dla testow aplikacji core."""

from typing import Any

import pytest


@pytest.fixture(autouse=True)
def _enable_db_access_for_all_tests(db: Any) -> None:  # noqa: ANN401
    """Fixture umozliwiajacy dostep do bazy danych we wszystkich testach."""
