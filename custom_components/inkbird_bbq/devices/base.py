"""Base types for INKBIRD BBQ devices."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class InkbirdBbqState:
    """Common state shared by supported INKBIRD BBQ devices."""

    model: str
    available: bool = False
    rssi: int | None = None
