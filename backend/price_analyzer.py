from backend.trade_api import TradeAPI
from backend.currency_service import CurrencyService

class PriceAnalyzer:
    def __init__(self, currency_service=None):
        self.currency_service = currency_service or CurrencyService()

    def analyze_gap(self, base_type, session_id=None):
        """
        Analyzes the price gap between Normal and Magic versions of a base item.
        """
        api = TradeAPI(session_id)
        
        # 1. Search Normal
        normal_query = {
            "status": {"option": "online"},
            "type": base_type,
            "filters": {
                "type_filters": {
                    "filters": {
                        "rarity": {"option": "normal"}
                    }
                }
            }
        }
        normal_avg = self._get_average_price(api, normal_query)
        
        # 2. Search Magic
        magic_query = {
            "status": {"option": "online"},
            "type": base_type,
            "filters": {
                "type_filters": {
                    "filters": {
                        "rarity": {"option": "magic"}
                    }
                }
            }
        }
        magic_avg = self._get_average_price(api, magic_query)
        
        return {
            "base_type": base_type,
            "normal_avg_chaos": round(normal_avg, 2),
            "magic_avg_chaos": round(magic_avg, 2),
            "gap_chaos": round(magic_avg - normal_avg, 2)
        }

    def _get_average_price(self, api, query):
        try:
            search_results = api.search(query)
            ids = search_results.get("result", [])[:10]  # Take top 10 for average
            if not ids:
                return 0.0
                
            fetch_results = api.fetch(ids, query_id=search_results.get("id"))
            items = fetch_results.get("result", [])
            
            prices = []
            for item in items:
                listing = item.get("listing", {})
                price_info = listing.get("price", {})
                amount = price_info.get("amount")
                currency = price_info.get("currency")
                
                if amount is not None and currency:
                    chaos_val = self.currency_service.normalize_to_chaos(amount, currency)
                    if chaos_val > 0:
                        prices.append(chaos_val)
            
            if not prices:
                return 0.0
                
            return sum(prices) / len(prices)
        except Exception as e:
            print(f"Error fetching data for query: {e}")
            return 0.0
