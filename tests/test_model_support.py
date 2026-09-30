"""Tests for model support boundaries and coordinator creation."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from custom_components.inkbird_bbq.const import (
    MODEL_INT_14_BW,
    MODEL_ISC_027BW,
    MODEL_TNT_11_B,
    PLANNED_MODELS,
    SUPPORTED_MODELS,
)
from custom_components.inkbird_bbq.coordinator import (
    Int14bwCoordinator,
    Isc027bwCoordinator,
    Tnt11bCoordinator,
    create_coordinator,
)


def test_supported_and_planned_models_are_separate() -> None:
    assert SUPPORTED_MODELS == {
        MODEL_ISC_027BW,
        MODEL_INT_14_BW,
        MODEL_TNT_11_B,
    }
    assert PLANNED_MODELS == set()
    assert SUPPORTED_MODELS.isdisjoint(PLANNED_MODELS)


@pytest.mark.parametrize(
    ("model", "coordinator_type"),
    [
        (MODEL_ISC_027BW, Isc027bwCoordinator),
        (MODEL_INT_14_BW, Int14bwCoordinator),
        (MODEL_TNT_11_B, Tnt11bCoordinator),
    ],
)
def test_create_coordinator_for_supported_model(
    model: str,
    coordinator_type: (
        type[Isc027bwCoordinator]
        | type[Int14bwCoordinator]
        | type[Tnt11bCoordinator]
    ),
) -> None:
    hass = MagicMock()
    entry = MagicMock()

    coordinator = create_coordinator(
        hass,
        entry,
        model=model,
        address="AA:BB:CC:DD:EE:FF",
    )

    assert isinstance(coordinator, coordinator_type)
