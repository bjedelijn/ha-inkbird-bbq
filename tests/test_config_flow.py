"""Tests for INKBIRD BBQ config-flow model matching."""

from custom_components.inkbird_bbq.config_flow import _model_from_name
from custom_components.inkbird_bbq.const import MODEL_INT_14_BW, MODEL_ISC_027BW


def test_known_models_match_exactly() -> None:
    assert _model_from_name("ISC-027BW") == MODEL_ISC_027BW
    assert _model_from_name("S27") == MODEL_ISC_027BW
    assert _model_from_name("INT-14-BW") == MODEL_INT_14_BW
    assert _model_from_name("INT-14-BW_WH") == MODEL_INT_14_BW


def test_unknown_and_similar_models_are_rejected() -> None:
    assert _model_from_name("INT-14S-BW") is None
    assert _model_from_name("INT-12I-BW") is None
    assert _model_from_name("ISC-027BW ") is None
    assert _model_from_name("S26") is None
    assert _model_from_name(None) is None
