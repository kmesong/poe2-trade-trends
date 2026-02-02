import time
import copy
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
                },
                "misc_filters": {
                    "filters": {
                        "ilvl": {"min": 81}
                    }
                }
            }
        }
        
        # Implement Price Ramp Logic
        start_price = max(1.0, normal_avg * 2.0)
        magic_avg = 0.0
        
        for attempt in range(15):
            current_min_price = start_price * (2 ** attempt)
            print(f"Attempting to fetch Magic items for {base_type} with min price: {current_min_price} (Attempt {attempt})")
            
            magic_avg = self._get_average_price(
                api, 
                magic_query, 
                item_validator=self._is_t1_magic,
                min_price_filter=current_min_price
            )
            
            if magic_avg > 0:
                print(f"Found Magic items! Average price: {magic_avg}")
                break
            else:
                print(f"No Magic items found at min price {current_min_price}")
        
        return {
            "base_type": base_type,
            "normal_avg_chaos": round(normal_avg, 2),
            "magic_avg_chaos": round(magic_avg, 2),
            "gap_chaos": round(magic_avg - normal_avg, 2)
        }

    def _is_t1_magic(self, item_entry):
        """
        Validator to check if a magic item has ONLY Tier 1 (P1 or S1) modifiers.
        Returns False if no modifiers are found or if any modifier is not Tier 1.
        
        Only checks 'explicit', 'fractured', and 'desecrated' mod groups.
        """
        # item_entry is the raw result from fetch()
        item = item_entry.get("item", {})
        mods = item.get("extended", {}).get("mods", {})
        
        has_any_mod = False
        target_groups = ["explicit", "fractured", "desecrated"]
        
        for group in target_groups:
            group_mods = mods.get(group, [])
            if not isinstance(group_mods, list):
                continue
                
            for mod in group_mods:
                has_any_mod = True
                tier = mod.get("tier", "")
                # If any mod is NOT T1, return False immediately
                if not (tier and (tier.startswith("P1") or tier.startswith("S1"))):
                    return False
        
        return has_any_mod

    def _get_average_price(self, api, query, item_validator=None, target_count=5, max_items_to_check=100, min_price_filter=None):
        try:
            if min_price_filter is not None:
                query = copy.deepcopy(query)
                # Ensure the nested path filters.trade_filters.filters.price.min exists
                if "filters" not in query:
                    query["filters"] = {}
                if "trade_filters" not in query["filters"]:
                    query["filters"]["trade_filters"] = {}
                if "filters" not in query["filters"]["trade_filters"]:
                    query["filters"]["trade_filters"]["filters"] = {}
                if "price" not in query["filters"]["trade_filters"]["filters"]:
                    query["filters"]["trade_filters"]["filters"]["price"] = {}
                query["filters"]["trade_filters"]["filters"]["price"]["min"] = min_price_filter

            search_results = api.search(query)
            all_ids = search_results.get("result", [])[:100]  # Get up to 100 IDs
            if not all_ids:
                return 0.0
                
            query_id = search_results.get("id")
            prices = []
            
            # Process in batches of 10
            for i in range(0, min(len(all_ids), max_items_to_check), 10):
                if len(prices) >= target_count:
                    break
                    
                batch_ids = all_ids[i:i+10]
                fetch_results = api.fetch(batch_ids, query_id=query_id)
                items = fetch_results.get("result", [])
                
                for item in items:
                    if item_validator and not item_validator(item):
                        continue
                        
                    listing = item.get("listing", {})
                    price_info = listing.get("price", {})
                    amount = price_info.get("amount")
                    currency = price_info.get("currency")
                    
                    if amount is not None and currency:
                        chaos_val = self.currency_service.normalize_to_chaos(amount, currency)
                        if chaos_val > 0:
                            prices.append(chaos_val)
                            if len(prices) >= target_count:
                                break
                
                # Sleep between batches if more items are needed and available
                if i + 10 < min(len(all_ids), max_items_to_check) and len(prices) < target_count:
                    time.sleep(0.5)
            
            if not prices:
                return 0.0
                
            return sum(prices) / len(prices)
        except Exception as e:
            print(f"Error fetching data for query: {e}")
            return 0.0
