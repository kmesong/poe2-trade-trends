import pytest
import requests_mock
from backend.trade_api import TradeAPI


def test_search_handles_502_retry():
    """Test that 502 Bad Gateway errors trigger retry logic."""
    api = TradeAPI()
    
    with requests_mock.Mocker() as m:
        # First call returns 502, second returns 200
        m.register_uri('POST', "https://www.pathofexile.com/api/trade2/search/poe2/Fate%20of%20the%20Vaal", [
            {'json': {'error': 'Bad Gateway'}, 'status_code': 502},
            {'json': {'result': ['item1'], 'id': 'query1'}, 'status_code': 200}
        ])
        
        # Mock time.sleep to avoid waiting in tests
        import time
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(time, "sleep", lambda x: None)
            result = api.search({})
        
        assert result["id"] == "query1"
        assert m.call_count == 2


def test_fetch_handles_502_retry():
    """Test that 502 errors in fetch also trigger retry logic."""
    api = TradeAPI()
    
    with requests_mock.Mocker() as m:
        # First call returns 502, second returns 200
        m.register_uri('GET', "https://www.pathofexile.com/api/trade2/fetch/item1?realm=poe2", [
            {'json': {'error': 'Bad Gateway'}, 'status_code': 502},
            {'json': {'result': [{"item": {}}]}, 'status_code': 200}
        ])
        
        import time
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(time, "sleep", lambda x: None)
            result = api.fetch(["item1"])
        
        assert "result" in result
        assert m.call_count == 2


def test_502_retry_uses_longer_delay_than_429():
    """Test that 502 errors use longer base delay (5s) vs 429 (2s)."""
    api = TradeAPI()
    
    sleep_times = []
    
    def mock_sleep(duration):
        sleep_times.append(duration)
    
    with requests_mock.Mocker() as m:
        # 502 on first attempt, success on second
        m.register_uri('POST', "https://www.pathofexile.com/api/trade2/search/poe2/Fate%20of%20the%20Vaal", [
            {'json': {'error': 'Bad Gateway'}, 'status_code': 502},
            {'json': {'result': ['item1'], 'id': 'query1'}, 'status_code': 200}
        ])
        
        import time
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(time, "sleep", mock_sleep)
            result = api.search({})
        
        # 502 should use 5s base delay (not 2s like 429)
        assert len(sleep_times) == 1
        assert sleep_times[0] == 5  # 502 base delay


def test_502_exponential_backoff():
    """Test that 502 retries use exponential backoff."""
    api = TradeAPI()
    
    sleep_times = []
    
    def mock_sleep(duration):
        sleep_times.append(duration)
    
    with requests_mock.Mocker() as m:
        # All attempts return 502 until last one succeeds
        responses = [{'json': {'error': 'Bad Gateway'}, 'status_code': 502} for _ in range(3)]
        responses.append({'json': {'result': ['item1'], 'id': 'query1'}, 'status_code': 200})
        
        m.register_uri('POST', "https://www.pathofexile.com/api/trade2/search/poe2/Fate%20of%20the%20Vaal", responses)
        
        import time
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(time, "sleep", mock_sleep)
            result = api.search({})
        
        # Exponential backoff: 5s, 10s, 20s (5 * 2^attempt for attempts 0, 1, 2)
        assert sleep_times == [5, 10, 20]


def test_429_retry_uses_shorter_delay():
    """Test that 429 errors use 2s base delay (vs 5s for 502)."""
    api = TradeAPI()
    
    sleep_times = []
    
    def mock_sleep(duration):
        sleep_times.append(duration)
    
    with requests_mock.Mocker() as m:
        m.register_uri('POST', "https://www.pathofexile.com/api/trade2/search/poe2/Fate%20of%20the%20Vaal", [
            {'json': {'error': 'Rate limited'}, 'status_code': 429},
            {'json': {'result': ['item1'], 'id': 'query1'}, 'status_code': 200}
        ])
        
        import time
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(time, "sleep", mock_sleep)
            result = api.search({})
        
        # 429 should use 2s base delay
        assert len(sleep_times) == 1
        assert sleep_times[0] == 2  # 429 base delay


def test_max_retries_on_502():
    """Test that after max retries (4), 502 error is raised."""
    import requests
    api = TradeAPI()
    
    with requests_mock.Mocker() as m:
        # All 4 attempts return 502
        m.register_uri('POST', "https://www.pathofexile.com/api/trade2/search/poe2/Fate%20of%20the%20Vaal",
                      json={'error': 'Bad Gateway'}, status_code=502)
        
        import time
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(time, "sleep", lambda x: None)
            
            with pytest.raises(requests.exceptions.HTTPError):
                api.search({})
        
        # Should have tried 4 times
        assert m.call_count == 4
