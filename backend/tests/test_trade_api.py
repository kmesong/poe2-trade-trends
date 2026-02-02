import pytest
import requests_mock
from backend.trade_api import TradeAPI

def test_search_uses_provided_session_id():
    session_id = "test_session_id"
    api = TradeAPI(session_id=session_id)
    
    with requests_mock.Mocker() as m:
        m.post("https://www.pathofexile.com/api/trade2/search/poe2/Fate%20of%20the%20Vaal", 
               json={"result": ["item1"], "id": "query1"})
        
        query = {"filters": {}}
        api.search(query)
        
        # Verify headers
        request = m.request_history[0]
        assert f"POESESSID={session_id}" in request.headers.get("Cookie", "")
        assert "Mozilla/5.0" in request.headers.get("User-Agent", "")

def test_fetch_uses_provided_session_id():
    session_id = "test_session_id"
    api = TradeAPI(session_id=session_id)
    
    with requests_mock.Mocker() as m:
        m.get("https://www.pathofexile.com/api/trade2/fetch/item1,item2?realm=poe2", 
              json={"result": []})
        
        api.fetch(["item1", "item2"])
        
        request = m.request_history[0]
        assert f"POESESSID={session_id}" in request.headers.get("Cookie", "")

def test_fetch_with_query_id():
    api = TradeAPI()
    query_id = "test_query"
    
    with requests_mock.Mocker() as m:
        # Note: params order might vary, but requests-mock handles it or we can check the url
        m.get("https://www.pathofexile.com/api/trade2/fetch/item1?realm=poe2&query=test_query", 
              json={"result": []})
        
        api.fetch(["item1"], query_id=query_id)
        
        request = m.request_history[0]
        assert "query=test_query" in request.url
        assert "realm=poe2" in request.url

def test_search_without_session_id():
    api = TradeAPI()
    
    with requests_mock.Mocker() as m:
        m.post("https://www.pathofexile.com/api/trade2/search/poe2/Fate%20of%20the%20Vaal", 
               json={"result": []})
        
        api.search({})
        
        request = m.request_history[0]
        assert "Cookie" not in request.headers or "POESESSID" not in request.headers.get("Cookie", "")
