import pytest
from backend.currency_service import CurrencyService

def test_get_rates():
    service = CurrencyService()
    rates = service.get_rates()
    assert "exalted" in rates
    assert rates["exalted"] == 1.0
    assert "chaos" in rates
    assert rates["chaos"] > 1.0  # Chaos is worth MORE than Exalted
    assert "divine" in rates
    assert rates["divine"] > 1.0  # Divine is worth MORE than Exalted

def test_normalize_to_exalted_known():
    service = CurrencyService()
    # 1 Exalted = 1.0
    assert service.normalize_to_exalted(1, "exalted") == 1.0
    # 1 Divine = 320 Ex (1 Divine is worth 320 Exalted)
    assert service.normalize_to_exalted(1, "divine") == 320.0
    # 1 Chaos = 7.8 Ex (1 Chaos is worth 7.8 Exalted)
    assert service.normalize_to_exalted(1, "chaos") == 7.8
    # 10 Alch = 39 Ex (10 * 3.9)
    assert service.normalize_to_exalted(10, "alch") == 39.0

def test_normalize_to_exalted_unknown():
    service = CurrencyService()
    assert service.normalize_to_exalted(10, "unknown_currency") == 0.0

def test_normalize_to_exalted_none():
    service = CurrencyService()
    assert service.normalize_to_exalted(10, None) == 0.0

def test_normalize_to_exalted_case_insensitive():
    service = CurrencyService()
    assert service.normalize_to_exalted(1, "DIVINE") == 320.0
    assert service.normalize_to_exalted(1, "CHAOS") == 7.8
