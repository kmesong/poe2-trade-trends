import pytest
from backend.currency_service import CurrencyService

def test_get_rates():
    service = CurrencyService()
    rates = service.get_rates()
    assert "chaos" in rates
    assert rates["chaos"] == 1.0
    assert "divine" in rates
    assert rates["divine"] > 1.0

def test_normalize_to_chaos_known():
    service = CurrencyService()
    # 1 Divine = 90 Chaos (based on hardcoded rates)
    assert service.normalize_to_chaos(1, "divine") == 90.0
    assert service.normalize_to_chaos(10, "chaos") == 10.0
    assert service.normalize_to_chaos(2, "alch") == 1.0

def test_normalize_to_chaos_unknown():
    service = CurrencyService()
    assert service.normalize_to_chaos(10, "unknown_currency") == 0.0

def test_normalize_to_chaos_none():
    service = CurrencyService()
    assert service.normalize_to_chaos(10, None) == 0.0

def test_normalize_to_chaos_case_insensitive():
    service = CurrencyService()
    assert service.normalize_to_chaos(1, "DIVINE") == 90.0
