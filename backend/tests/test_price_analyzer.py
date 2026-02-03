import pytest
from unittest.mock import MagicMock, patch
from backend.price_analyzer import PriceAnalyzer

@pytest.fixture
def mock_currency_service():
    service = MagicMock()
    # Mock normalize_to_exalted: 1 unit of any currency = 0.1 exalts for simplicity in tests
    service.normalize_to_exalted.side_effect = lambda amount, currency: amount * 0.1 if currency == "divine" else float(amount) * 0.00556  # chaos converted
    return service

@patch("backend.price_analyzer.TradeAPI")
def test_analyze_gap_success(MockTradeAPI, mock_currency_service):
    # Setup mocks
    mock_api = MockTradeAPI.return_value
    
    # Mock search results
    mock_api.search.side_effect = [
        {"result": ["normal1", "normal2"], "id": "search_normal"}, # Generic normal search
        {"result": ["craft1", "craft2"], "id": "search_craft"},   # Crafting base search
        {"result": ["magic1", "magic2"], "id": "search_magic"}      # Magic search
    ]
    
    # Mock fetch results
    mock_api.fetch.side_effect = [
        { # Generic normal
            "result": [
                {"listing": {"price": {"amount": 5, "currency": "chaos"}}},
                {"listing": {"price": {"amount": 7, "currency": "chaos"}}}
            ]
        },
        { # Crafting normal
            "result": [
                {"listing": {"price": {"amount": 10, "currency": "chaos"}}},
                {"listing": {"price": {"amount": 12, "currency": "chaos"}}}
            ]
        },
        { # Magic
            "result": [
                {"listing": {"price": {"amount": 1, "currency": "divine"}}, "item": {"extended": {"mods": {"explicit": [{"tier": "P1"}, {"tier": "S1"}]}}}}, # 1 divine = 0.1 exalt
                {"listing": {"price": {"amount": 1.2, "currency": "divine"}}, "item": {"extended": {"mods": {"explicit": [{"tier": "P1"}, {"tier": "S1"}]}}}} # 1.2 divine = 0.12 exalt
            ]
        }
    ]
    
    analyzer = PriceAnalyzer(currency_service=mock_currency_service)
    result = analyzer.analyze_gap("Expert Dualnaught Bow")
    
    # Generic Normal avg: (5 + 7) / 2 * 0.00556 = 0.03336 exalts
    # Crafting Normal avg: (10 + 12) / 2 * 0.00556 = 0.06116 exalts
    # Magic avg: (1 + 1.2) / 2 * 0.1 = 0.11 exalts
    # Gap: 0.11 - 0.06116 = 0.04884 exalts
    
    assert result["base_type"] == "Expert Dualnaught Bow"
    assert result["normal_avg_chaos"] == pytest.approx(0.03, rel=0.1)
    assert result["crafting_avg_chaos"] == pytest.approx(0.06, rel=0.1)
    assert result["magic_avg_chaos"] == pytest.approx(0.11, rel=0.1)
    assert result["gap_chaos"] == pytest.approx(0.05, rel=0.1)

@patch("backend.price_analyzer.TradeAPI")
def test_analyze_gap_no_results(MockTradeAPI, mock_currency_service):
    mock_api = MockTradeAPI.return_value
    mock_api.search.return_value = {"result": []}
    
    analyzer = PriceAnalyzer(currency_service=mock_currency_service)
    result = analyzer.analyze_gap("Unknown Item")
    
    assert result["normal_avg_chaos"] == 0.0
    assert result["crafting_avg_chaos"] == 0.0
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

@patch("backend.price_analyzer.TradeAPI")
@patch("time.sleep")
def test_get_average_price_recursive(mock_sleep, MockTradeAPI, mock_currency_service):
    mock_api = MockTradeAPI.return_value
    
    # Mock search results: 20 IDs
    mock_api.search.return_value = {"result": [f"item{i}" for i in range(20)], "id": "search_recursive"}
    
    # Batch 1: Items that fail validation (T2 mods)
    batch1_items = [{"id": f"item{i}", "item": {"extended": {"mods": {"explicit": [{"tier": "P2"}]}}}} for i in range(10)]
    # Batch 2: Items that pass validation (T1 mods)
    batch2_items = [
        {"listing": {"price": {"amount": 20, "currency": "chaos"}}, "item": {"extended": {"mods": {"explicit": [{"tier": "P1"}]}}}} 
        for i in range(5)
    ]
    
    mock_api.fetch.side_effect = [
        {"result": batch1_items},
        {"result": batch2_items}
    ]
    
    analyzer = PriceAnalyzer(currency_service=mock_currency_service)
    
    # We test _get_average_price directly to verify recursive fetching logic
    query = {"some": "query"}
    avg = analyzer._get_average_price(mock_api, query, item_validator=analyzer._is_t1_magic)
    
    # 20 chaos = 20 * 0.00556 = 0.1112 exalts
    assert avg == pytest.approx(0.1112, rel=0.01)
    assert mock_api.fetch.call_count == 2
    assert mock_sleep.call_count == 1

@patch("backend.price_analyzer.TradeAPI")
def test_analyze_gap_price_ramp(MockTradeAPI, mock_currency_service):
    mock_api = MockTradeAPI.return_value
    
    # 1. Normal search returns 10 chaos avg
    # 2. Normal craft search returns 15 chaos avg
    # 3. Magic attempt 0 (min_price=30): returns no items
    # 4. Magic attempt 1 (min_price=60): returns 50 chaos avg
    
    mock_api.search.side_effect = [
        {"result": ["normal1"], "id": "search_normal"}, # Generic search
        {"result": ["craft1"], "id": "search_craft"},   # Craft search
        {"result": [], "id": "search_magic_0"},         # Magic attempt 0
        {"result": ["magic1"], "id": "search_magic_1"}  # Magic attempt 1
    ]
    
    mock_api.fetch.side_effect = [
        { # Generic normal
            "result": [
                {"listing": {"price": {"amount": 10, "currency": "chaos"}}}
            ]
        },
        { # Crafting normal
            "result": [
                {"listing": {"price": {"amount": 15, "currency": "chaos"}}}
            ]
        },
        # Fetch for magic1
        {
            "result": [
                {
                    "listing": {"price": {"amount": 50, "currency": "chaos"}},
                    "item": {"extended": {"mods": {"explicit": [{"tier": "P1"}, {"tier": "S1"}]}}}
                }
            ]
        }
    ]
    
    analyzer = PriceAnalyzer(currency_service=mock_currency_service)
    result = analyzer.analyze_gap("Ramp Bow")
    
    # 10 chaos = 10 * 0.00556 = 0.0556 exalts
    # 15 chaos = 15 * 0.00556 = 0.0834 exalts
    # 50 chaos = 50 * 0.00556 = 0.278 exalts
    assert result["normal_avg_chaos"] == pytest.approx(0.06, rel=0.1)
    assert result["crafting_avg_chaos"] == pytest.approx(0.08, rel=0.1)
    assert result["magic_avg_chaos"] == pytest.approx(0.28, rel=0.1)
    assert mock_api.search.call_count == 4 # 1 normal + 1 craft + 2 magic attempts

def test_is_t1_magic_ignores_implicits():
    analyzer = PriceAnalyzer()
    
    # Mock item with implicit (no tier) and T1 explicit
    mock_item = {
        "item": {
            "extended": {
                "mods": {
                    "implicit": [{"text": "Some implicit"}], # Should be ignored
                    "explicit": [{"tier": "P1"}]
                }
            }
        }
    }
    
    assert analyzer._is_t1_magic(mock_item) is True

