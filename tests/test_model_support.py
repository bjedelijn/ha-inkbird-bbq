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
    create_coordinator,
)


def test_supported_and_planned_models_are_separate() -> None:
    assert SUPPORTED_MODELS == {MODEL_ISC_027BW, MODEL_INT_14_BW}
    assert PLANNED_MODELS == {MODEL_TNT_11_B}
    assert SUPPORTED_MODELS.isdisjoint(PLANNED_MODELS)


@pytest.mark.parametrize(
    ("model", "coordinator_type"),
    [
        (MODEL_ISC_027BW, Isc027bwCoordinator),
        (MODEL_INT_14_BW, Int14bwCoordinator),
    ],
)
def test_create_coordinator_for_supported_model(
    model: str,
    coordinator_type: type[Isc027bwCoordinator] | type[Int14bwCoordinator],
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


def test_tnt11b_cannot_be_created_before_protocol_support() -> None:
    with pytest.raises(ValueError, match="Unsupported INKBIRD BBQ model: TNT-11-B"):
        create_coordinator(
            MagicMock(),
            MagicMock(),
            model=MODEL_TNT_11_B,
            address="AA:BB:CC:DD:EE:FF",
        )
