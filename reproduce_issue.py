import sys
import os
import json

# Add current directory to path so we can import backend
sys.path.append(os.getcwd())

from backend.trade_api import TradeAPI

def test_search():
    api = TradeAPI()
    
    # Try 1: Search as "type"
    print("--- Test 1: Search as 'type' ---")
    query_type = {
        "status": {"option": "online"},
        "type": "Topaz Charm",
        "filters": {}
    }
    try:
        result = api.search(query_type)
        print("Success:", json.dumps(result, indent=2))
    except Exception as e:
        print("Failed:", str(e))
        if hasattr(e, 'response') and e.response is not None:
             print("Response:", e.response.text)

    # Try 2: Search as "term" (text search)
    print("\n--- Test 2: Search as 'term' ---")
    query_term = {
        "status": {"option": "online"},
        "query": {
            "term": "Topaz Charm"
        },
        "filters": {}
    }
    try:
        result = api.search(query_term)
        print("Success:", json.dumps(result, indent=2))
    except Exception as e:
        print("Failed:", str(e))

if __name__ == "__main__":
    test_search()
