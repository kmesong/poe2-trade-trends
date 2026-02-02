import pytest
from unittest.mock import MagicMock, patch
from backend.price_analyzer import PriceAnalyzer

@pytest.fixture
def mock_currency_service():
    service = MagicMock()
    # Mock normalize_to_chaos: 1 unit of any currency = 10 chaos for simplicity in tests
    service.normalize_to_chaos.side_effect = lambda amount, currency: amount * 10.0 if currency == "divine" else float(amount)
    return service

@patch("backend.price_analyzer.TradeAPI")
def test_analyze_gap_success(MockTradeAPI, mock_currency_service):
    # Setup mocks
    mock_api = MockTradeAPI.return_value
    
    # Mock search results
    mock_api.search.side_effect = [
        {"result": ["normal1", "normal2"], "id": "search_normal"}, # Normal search
        {"result": ["magic1", "magic2"], "id": "search_magic"}      # Magic search
    ]
    
    # Mock fetch results for Normal
    mock_api.fetch.side_effect = [
        {
            "result": [
                {"listing": {"price": {"amount": 5, "currency": "chaos"}}},
                {"listing": {"price": {"amount": 7, "currency": "chaos"}}}
            ]
        },
        {
            "result": [
                {"listing": {"price": {"amount": 1, "currency": "divine"}}, "extended": {"mods": {"explicit": [{"tier": "P1"}]}}}, # 10 chaos
                {"listing": {"price": {"amount": 1.2, "currency": "divine"}}, "extended": {"mods": {"explicit": [{"tier": "S1"}]}}} # 12 chaos
            ]
        }
    ]
    
    analyzer = PriceAnalyzer(currency_service=mock_currency_service)
    result = analyzer.analyze_gap("Expert Dualnaught Bow")
    
    # Normal avg: (5 + 7) / 2 = 6
    # Magic avg: (10 + 12) / 2 = 11
    # Gap: 11 - 6 = 5
    
    assert result["base_type"] == "Expert Dualnaught Bow"
    assert result["normal_avg_chaos"] == 6.0
    assert result["magic_avg_chaos"] == 11.0
    assert result["gap_chaos"] == 5.0

@patch("backend.price_analyzer.TradeAPI")
def test_analyze_gap_no_results(MockTradeAPI, mock_currency_service):
    mock_api = MockTradeAPI.return_value
    mock_api.search.return_value = {"result": []}
    
    analyzer = PriceAnalyzer(currency_service=mock_currency_service)
    result = analyzer.analyze_gap("Unknown Item")
    
    assert result["normal_avg_chaos"] == 0.0
    assert result["magic_avg_chaos"] == 0.0
    assert result["gap_chaos"] == 0.0

@patch("backend.price_analyzer.TradeAPI")
def test_analyze_gap_missing_price_info(MockTradeAPI, mock_currency_service):
    mock_api = MockTradeAPI.return_value
    mock_api.search.return_value = {"result": ["item1"], "id": "search1"}
    mock_api.fetch.return_value = {
        "result": [
            {"listing": {}} # Missing price
        ]
    }
    
    analyzer = PriceAnalyzer(currency_service=mock_currency_service)
    result = analyzer.analyze_gap("Item with no price")
    
    assert result["normal_avg_chaos"] == 0.0
    assert result["magic_avg_chaos"] == 0.0
