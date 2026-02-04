import time
import copy
from backend.trade_api import TradeAPI
from backend.currency_service import CurrencyService

class PriceAnalyzer:
    def __init__(self, currency_service=None):
        self.currency_service = currency_service or CurrencyService()

    def analyze_gap(self, base_type, session_id=None, exclusions=None):
        """
        Analyzes the price gap between Normal and Magic versions of a base item.
        """
        api = TradeAPI(session_id)
        
        # 1. Search Normal (base search - all normal items)
        normal_query = {
            "status": {"option": "securable"},
            "type": base_type,
            "filters": {
                "type_filters": {
                    "filters": {
                        "rarity": {"option": "normal"}
                    }
                }
            }
        }
        normal_result = self._get_search_result(api, normal_query)
        normal_avg, normal_mods = self._calculate_average_from_result(api, normal_result, exclusions=exclusions)
        search_id = normal_result.get("id") if normal_result else None
        
        # 2. Search Normal with filters (ilvl 82, min 2 rune sockets) - for crafting base price
        normal_craft_query = {
            "status": {"option": "securable"},
            "type": base_type,
            "filters": {
                "type_filters": {
                    "filters": {
                        "rarity": {"option": "normal"}
                    }
                },
                "misc_filters": {
                    "filters": {
                        "ilvl": {"min": 82}
                    }
                },
                "equipment_filters": {
                    "filters": {
                        "rune_sockets": {"min": 2}
                    }
                }
            }
        }
        normal_craft_result = self._get_search_result(api, normal_craft_query)
        normal_craft_avg, _ = self._calculate_average_from_result(api, normal_craft_result, exclusions=exclusions)
        crafting_search_id = normal_craft_result.get("id") if normal_craft_result else None
        
        # 3. Search Magic
        magic_query = {
            "status": {"option": "securable"},
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
        
        # Implement Price Ramp Logic - faster progression: 1, 100, 250, 500, 1000, 5000
        start_price = max(1.0, normal_avg * 2.0)
        magic_avg = 0.0
        magic_search_id = None
        magic_mods = []  # Initialize to avoid unbound error
        
        # Custom price progression
        price_progression = [1, 100, 250, 500, 1000, 5000]
        # Scale the progression relative to start_price
        max_price = price_progression[-1]
        scale_factor = start_price / max_price if start_price > max_price else 1.0
        
        for attempt, base_price in enumerate(price_progression):
            # Scale the price point
            current_min_price = base_price * scale_factor
            current_min_price = max(current_min_price, price_progression[0])  # Ensure we start at least at the first tier
            
            print(f"Attempting to fetch Magic items for {base_type} with min price: {current_min_price:.2f} (Attempt {attempt + 1})")

            # Apply min price filter to query and execute search
            filtered_query = copy.deepcopy(magic_query)
            if "filters" not in filtered_query:
                filtered_query["filters"] = {}
            if "trade_filters" not in filtered_query["filters"]:
                filtered_query["filters"]["trade_filters"] = {}
            if "filters" not in filtered_query["filters"]["trade_filters"]:
                filtered_query["filters"]["trade_filters"]["filters"] = {}
            if "price" not in filtered_query["filters"]["trade_filters"]["filters"]:
                filtered_query["filters"]["trade_filters"]["filters"]["price"] = {}
            
            # Explicitly set the min price and currency option
            filtered_query["filters"]["trade_filters"]["filters"]["price"]["min"] = current_min_price
            filtered_query["filters"]["trade_filters"]["filters"]["price"]["option"] = "exalted"
            
            # Ensure max price is not set (unless we want to?)
            if "max" in filtered_query["filters"]["trade_filters"]["filters"]["price"]:
                del filtered_query["filters"]["trade_filters"]["filters"]["price"]["max"]

            magic_result = self._get_search_result(api, filtered_query)
            magic_search_id = magic_result.get("id") if magic_result else None

            magic_avg, magic_mods = self._calculate_average_from_result(
                api,
                magic_result,
                item_validator=self._is_t1_magic,
                exclusions=exclusions,
                min_mod_count=2
            )

            if magic_avg > 0:
                print(f"Found Magic items! Average price: {magic_avg}")
                break
            else:
                print(f"No Magic items found at min price {current_min_price}")
        
        return {
            "base_type": base_type,
            "normal_avg_ex": round(normal_avg, 2),
            "crafting_avg_ex": round(normal_craft_avg, 2),
            "magic_avg_ex": round(magic_avg, 2),
            "gap_ex": round(magic_avg - normal_craft_avg, 2),
            "search_id": search_id,
            "magic_search_id": magic_search_id,
            "crafting_search_id": crafting_search_id,
            "normal_modifiers": normal_mods,
            "magic_modifiers": magic_mods
        }

    def _is_t1_magic(self, item_entry):
        """
        Validator to check if a magic item has ONLY Tier 1 (P1 or S1) modifiers.
        Returns False if no modifiers are found or if any modifier is not Tier 1.
        
        Only checks 'explicit', 'fractured', and 'desecrated' mod groups.
        """
        # item_entry is the raw result from fetch()
        item = item_entry.get("item", {})
        if not isinstance(item, dict):
            return False
            
        extended = item.get("extended", {})
        if not isinstance(extended, dict):
            return False
            
        mods = extended.get("mods", {})
        if not isinstance(mods, dict):
            return False
            
        has_any_mod = False
        target_groups = ["explicit", "fractured", "desecrated"]
        
        for group in target_groups:
            group_mods = mods.get(group, [])
            if not isinstance(group_mods, list):
                continue
                
            for mod in group_mods:
                has_any_mod = True
                tier = mod.get("tier", "")
                print(f"DEBUG: Found mod tier='{tier}' in group '{group}'")
                # If any mod is NOT T1, return False immediately
                if not (tier and (tier.startswith("P1") or tier.startswith("S1"))):
                    print(f"DEBUG: Rejected - tier '{tier}' is not P1 or S1")
                    return False
        
        print(f"DEBUG: Accepted - all mods are P1 or S1")
        return has_any_mod

    def _get_search_result(self, api, query):
        """Execute search and return full result (includes search ID)."""
        try:
            result = api.search(query)
            if isinstance(result, list):
                return {"result": result, "total": len(result)}
            return result or {}
        except Exception as e:
            error_msg = str(e)
            if "502" in error_msg or "Bad Gateway" in error_msg:
                print(f"Error searching (502 Bad Gateway): {e}")
            elif "429" in error_msg or "Rate limit" in error_msg.lower():
                print(f"Error searching (429 Rate Limited): {e}")
            else:
                print(f"Error searching: {e}")
            return {}

    def _calculate_average_from_result(self, api, search_result, item_validator=None, target_count=5, max_items_to_check=100, exclusions=None, min_mod_count=0, extractor_func=None):
        """
        Calculate average price and collect modifier data from a search result.
        Returns tuple of (average_price, modifiers_list).
        """
        print(f"DEBUG: _calculate_average_from_result called with search_result type={type(search_result)}")
        print(f"DEBUG: search_result content (truncated): {str(search_result)[:500]}")
        try:
            if isinstance(search_result, list):
                all_ids = search_result[:100]
            else:
                all_ids = search_result.get("result", [])[:100]
                
            if not all_ids:
                return 0.0, []
                
            query_id = search_result.get("id") if isinstance(search_result, dict) else None
            prices = []
            modifiers = []
            i = 0  # Initialize for potential sleep check
            
            # Use provided extractor or default to _extract_modifiers
            extract_func = extractor_func or self._extract_modifiers
            
            # Process in batches of 10
            for i in range(0, min(len(all_ids), max_items_to_check), 10):
                if len(prices) >= target_count:
                    break
                    
                batch_ids = all_ids[i:i+10]
                fetch_results = api.fetch(batch_ids, query_id=query_id)
                print(f"DEBUG: fetch_results type={type(fetch_results)}")
                print(f"DEBUG: fetch_results content (truncated): {str(fetch_results)[:500]}")
                
                if isinstance(fetch_results, list):
                    items = fetch_results
                else:
                    items = fetch_results.get("result", [])
                
                print(f"DEBUG: Processing {len(items)} items from fetch")
                for idx, item in enumerate(items):
                    print(f"DEBUG: Item[{idx}] type={type(item)}")
                    if not isinstance(item, dict):
                        print(f"DEBUG: Skipping non-dict item at index {idx}: {str(item)[:200]}")
                        continue
                        
                    # Extract modifiers/attributes from this item
                    item_mods = extract_func(item)
                    if item_mods:
                        # Filter exclusions
                        if exclusions:
                            filtered_mods = []
                            for mod in item_mods:
                                is_excluded = False
                                for ex in exclusions:
                                    # Check type
                                    if ex.mod_type and ex.mod_type != mod['mod_type']: continue
                                    # Check tier
                                    if ex.mod_tier and ex.mod_tier != mod['tier']: continue
                                    # Check name pattern
                                    if ex.mod_name_pattern:
                                        import re
                                        # Convert SQL LIKE % to regex .*
                                        pattern = ex.mod_name_pattern.replace('%', '.*')
                                        if not re.search(pattern, mod['name'], re.IGNORECASE): continue
                                    
                                    is_excluded = True
                                    break
                                
                                if not is_excluded:
                                    filtered_mods.append(mod)
                            item_mods = filtered_mods

                        # If all mods were excluded (and we originally had mods), skip this item entirely
                        # This prevents items with only excluded mods from affecting the average price
                        if not item_mods:
                            continue
                        
                        # Verify minimum modifier count (after exclusions)
                        if len(item_mods) < min_mod_count:
                            continue

                        modifiers.extend(item_mods)

                    if item_validator and not item_validator(item):
                        continue
                        
                    listing = item.get("listing", {})
                    price_info = listing.get("price", {})
                    amount = price_info.get("amount")
                    currency = price_info.get("currency")
                    
                    if amount is not None and currency:
                        exalts_val = self.currency_service.normalize_to_exalted(amount, currency)
                        if exalts_val > 0:
                            prices.append(exalts_val)
                            if len(prices) >= target_count:
                                break
            
            # Sleep between batches
            if i + 10 < min(len(all_ids), max_items_to_check) and len(prices) < target_count:
                time.sleep(0.5)
            
            if len(prices) < target_count:
                return 0.0, []
                
            avg_price = sum(prices) / len(prices)
            
            # Deduplicate modifiers
            # Keep the one with the best display text (longest/most descriptive)
            unique_mods = {}
            for mod in modifiers:
                key = (mod['name'], mod['tier'], mod['mod_type'])
                if key not in unique_mods:
                    unique_mods[key] = mod
                else:
                    # If existing has no display text (or just name), and new one has good text, replace
                    current = unique_mods[key]
                    curr_text = current.get('display_text', '')
                    new_text = mod.get('display_text', '')
                    
                    # If new text is better (longer is a simple heuristic for "not just the name")
                    if len(new_text) > len(curr_text):
                        unique_mods[key] = mod
                        
            return avg_price, list(unique_mods.values())
        except AttributeError as e:
            import traceback
            print(f"CRITICAL AttributeError in _calculate_average_from_result: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            print(f"Problematic search_result type: {type(search_result)}")
            print(f"Problematic search_result: {str(search_result)[:1000]}")
            return 0.0, []
        except Exception as e:
            print(f"Error calculating average: {e}")
            return 0.0, []

    def _extract_attributes(self, item):
        """
        Helper to capture non-mod data (ilvl, sockets, etc.) plus explicit modifiers.
        Returns a list of modifier-like dictionaries.
        """
        # Start with standard modifiers
        mods = self._extract_modifiers(item)
        
        item_data = item.get("item", {})
        if not isinstance(item_data, dict):
            return mods
            
        rarity = item_data.get("rarity", "unknown")
        item_name = item_data.get("name", "")
        
        def add_prop(name, value, p_type="property"):
            mods.append({
                "name": name,
                "tier": "",
                "mod_type": p_type,
                "rarity": rarity,
                "item_name": item_name,
                "display_text": str(value),
                "magnitude_min": None,
                "magnitude_max": None
            })

        # ILVL
        if "ilvl" in item_data:
            add_prop("Item Level", item_data["ilvl"])
            
        # Rarity
        if "rarity" in item_data:
            add_prop("Rarity", item_data["rarity"])
            
        # Sockets & Links
        sockets = item_data.get("sockets", [])
        if sockets:
            add_prop("Sockets", len(sockets))
            
            # Calculate max links
            groups = {}
            for s in sockets:
                g = s.get("group", 0)
                groups[g] = groups.get(g, 0) + 1
            max_links = max(groups.values()) if groups else 0
            add_prop("Links", max_links)
            
        # Flags
        if item_data.get("corrupted"):
            add_prop("Corrupted", "Yes")
        if item_data.get("identified"):
            add_prop("Identified", "Yes")
        if item_data.get("mirrored"):
            add_prop("Mirrored", "Yes")
            
        # Quality
        properties = item_data.get("properties", [])
        for prop in properties:
            if prop.get("name") == "Quality":
                values = prop.get("values", [])
                if values and len(values) > 0:
                    # value is usually ["+20%", 1]
                    add_prop("Quality", values[0][0])
                    
        # Prefixes/Suffixes count
        extended = item_data.get("extended", {})
        if isinstance(extended, dict):
            if "prefixes" in extended:
                add_prop("Prefix Count", extended["prefixes"], "stat")
            if "suffixes" in extended:
                add_prop("Suffix Count", extended["suffixes"], "stat")
            
        return mods

    def analyze_distribution(self, base_type, session_id=None, num_buckets=10):
        """
        Analyzes the price distribution of a base item type.
        """
        api = TradeAPI(session_id)
        
        # Base query for all searches
        # Using 'term' instead of 'type' to handle both base types and unique names gracefully
        base_query = {
            "status": {"option": "securable"},
            "term": base_type
        }
        
        # 1. Find Min Price (sort price asc, fetch top 5)
        min_query = copy.deepcopy(base_query)
        min_result = self._get_search_result(api, min_query)
        min_price, _ = self._calculate_average_from_result(api, min_result, target_count=5)
        
        # 2. Find Max Price (sort price desc, fetch top 5)
        max_query = copy.deepcopy(base_query)
        max_query["sort"] = {"price": "desc"}
        max_result = self._get_search_result(api, max_query)
        max_price, _ = self._calculate_average_from_result(api, max_result, target_count=5)
        
        # Ensure valid range
        if max_price < min_price:
            max_price = min_price
        
        # 3. Create Buckets
        buckets_data = []
        if max_price > min_price:
            interval = (max_price - min_price) / num_buckets
        else:
            interval = 0.1 # Default small spread if no variation found
            
        for i in range(num_buckets):
            b_min = min_price + (i * interval)
            b_max = min_price + ((i + 1) * interval)
            
            # Avoid tiny overlaps or floating point issues
            if i == num_buckets - 1 and max_price > 0:
                b_max = max(b_max, max_price * 1.01)
                
            # Final safety check for price range validity
            if b_max <= b_min:
                b_max = b_min + 0.01
                
            bucket_query = copy.deepcopy(base_query)
            if "filters" not in bucket_query: bucket_query["filters"] = {}
            if "trade_filters" not in bucket_query["filters"]:
                bucket_query["filters"]["trade_filters"] = {}
            if "filters" not in bucket_query["filters"]["trade_filters"]:
                bucket_query["filters"]["trade_filters"]["filters"] = {}
                
            bucket_query["filters"]["trade_filters"]["filters"]["price"] = {
                "min": b_min,
                "max": b_max,
                "option": "exalted"
            }
            
            # Execute search for bucket
            result = self._get_search_result(api, bucket_query)
            total = result.get("total", 0)
            
            avg_val = 0.0
            common_stats = []
            
            if total > 0:
                # Fetch a sample to get attributes and average price in this bucket
                # Use _extract_attributes to get stats
                avg_val, common_stats = self._calculate_average_from_result(
                    api, result, 
                    target_count=5, # Sample 5 items
                    extractor_func=self._extract_attributes
                )
            
            buckets_data.append({
                "min": round(b_min, 2),
                "max": round(b_max, 2),
                "count": total,
                "avg_price": round(avg_val, 2),
                "common_stats": common_stats
            })
            
            # Rate limit protection between buckets
            time.sleep(2)
            
        return {
            "base_type": base_type,
            "min_price": round(min_price, 2),
            "max_price": round(max_price, 2),
            "buckets": buckets_data
        }


    def _extract_modifiers(self, item):
        """
        Extract T1 (P1/S1) modifiers from an item with display labels.
        Returns list of modifier objects with display text.
        """
        modifiers = []
        item_data = item.get("item", {})
        
        # Handle cases where item_data might be a list or non-dict (malformed API response)
        if not isinstance(item_data, dict):
            return []
            
        rarity = item_data.get("rarity", "unknown")
        item_name = item_data.get("name", "")
        
        extended = item_data.get("extended", {})
        if not isinstance(extended, dict):
            return []
            
        mods = extended.get("mods", {})
        if not isinstance(mods, dict):
            return []
            
        target_groups = ["explicit", "implicit", "fractured", "desecrated"]
        
        for group in target_groups:
            group_mods = mods.get(group, [])
            if not isinstance(group_mods, list):
                continue
            
            for mod in group_mods:
                tier = mod.get("tier", "")
                
                # Only capture T1 modifiers (P1 or S1)
                if not (tier and (tier.startswith("P1") or tier.startswith("S1"))):
                    continue
                
                # Get display text - prefer 'text' field, otherwise construct from magnitudes
                display_text = mod.get("text", "").strip()
                
                if not display_text:
                    # Construct display text from magnitudes only
                    magnitudes = mod.get("magnitudes", [])
                    
                    if magnitudes and isinstance(magnitudes, list) and len(magnitudes) > 0:
                        mag = magnitudes[0]
                        if isinstance(mag, dict):
                            min_val = mag.get("min")
                            max_val = mag.get("max")
                            
                            if min_val is not None and max_val is not None:
                                display_text = f"{min_val} to {max_val}"
                            elif min_val is not None:
                                display_text = str(min_val)
                            elif max_val is not None:
                                display_text = str(max_val)
                
                # Fallback: if still no display text, try to match with item.explicitMods
                # This is common for Charms where extended data lacks text but top-level explicitMods has it
                if True: # Always try to improve display text from explicitMods if it's just numbers
                    magnitudes = mod.get("magnitudes", [])
                    if magnitudes and len(magnitudes) > 0:
                        mag = magnitudes[0]
                        min_v = float(mag.get("min", 0)) if mag.get("min") is not None else -999999
                        max_v = float(mag.get("max", 0)) if mag.get("max") is not None else 999999
                        
                        # Get candidate strings based on mod type
                        # If mod_type is 'explicit', look in 'explicitMods'
                        # If 'implicit', look in 'implicitMods'
                        candidate_strings = []
                        if group == 'explicit':
                            candidate_strings = item_data.get('explicitMods', [])
                        elif group == 'implicit':
                            candidate_strings = item_data.get('implicitMods', [])
                            
                        # Try to match values
                        import re
                        for candidate in candidate_strings:
                            # Extract all numbers from the string
                            # Handle decimals and negative numbers
                            nums = [float(x) for x in re.findall(r'-?\d+(?:\.\d+)?', candidate)]
                            
                            # Check if ANY number in the string falls within the magnitude range
                            # Use a small epsilon for float comparison if needed, but exact match is usually fine for these APIs
                            is_match = False
                            if not nums:
                                continue

                            for num in nums:
                                # Check normal range
                                if min_v <= num <= max_v:
                                    is_match = True
                                    break
                                # Check absolute values (for "reduced" mods which are negative in data but positive in text)
                                if min_v < 0 and max_v < 0:
                                    if abs(max_v) <= num <= abs(min_v):
                                        is_match = True
                                        break
                            
                            if is_match:
                                display_text = candidate
                                break

                # Fallback: if still no display text, use the mod name
                if not display_text:
                    display_text = mod.get("name", "Unknown Modifier")

                # Get magnitude values for reference (re-extracting safely)
                magnitudes = mod.get("magnitudes", [])
                min_val = None
                max_val = None
                if magnitudes and isinstance(magnitudes, list) and len(magnitudes) > 0:
                    mag = magnitudes[0]
                    if isinstance(mag, dict):
                        min_val = float(mag.get("min", 0)) if mag.get("min") else None
                        max_val = float(mag.get("max", 0)) if mag.get("max") else None

                if display_text:
                    modifiers.append({
                        "name": mod.get("name", ""),
                        "tier": tier,
                        "mod_type": group,
                        "rarity": rarity,
                        "item_name": item_name,
                        "display_text": display_text,
                        "magnitude_min": min_val,
                        "magnitude_max": max_val
                    })
        
        return modifiers

    def _get_average_price(self, api, query, item_validator=None, target_count=5, max_items_to_check=100, min_price_filter=None):
        # ... existing implementation for backward compatibility ...
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
            if isinstance(search_results, list):
                all_ids = search_results[:100]
            else:
                all_ids = search_results.get("result", [])[:100]  # Get up to 100 IDs
                
            if not all_ids:
                return 0.0
                
            query_id = search_results.get("id") if isinstance(search_results, dict) else None
            prices = []
            
            # Process in batches of 10
            for i in range(0, min(len(all_ids), max_items_to_check), 10):
                if len(prices) >= target_count:
                    break
                    
                batch_ids = all_ids[i:i+10]
                fetch_results = api.fetch(batch_ids, query_id=query_id)
                
                if isinstance(fetch_results, list):
                    items = fetch_results
                else:
                    items = fetch_results.get("result", [])
                
                for item in items:
                    if not isinstance(item, dict):
                        continue
                        
                    if item_validator and not item_validator(item):
                        continue
                        
                    listing = item.get("listing", {})
                    price_info = listing.get("price", {})
                    amount = price_info.get("amount")
                    currency = price_info.get("currency")
                    
                    if amount is not None and currency:
                        exalts_val = self.currency_service.normalize_to_exalted(amount, currency)
                        if exalts_val > 0:
                            prices.append(exalts_val)
                            if len(prices) >= target_count:
                                break
                
                # Sleep between batches if more items are needed and available
                if i + 10 < min(len(all_ids), max_items_to_check) and len(prices) < target_count:
                    time.sleep(0.5)
            
            if len(prices) < target_count:
                return 0.0
                
            return sum(prices) / len(prices)
        except Exception as e:
            error_msg = str(e)
            if "502" in error_msg or "Bad Gateway" in error_msg:
                print(f"Error fetching data for query (502 Bad Gateway): {e}")
            elif "429" in error_msg or "Rate limit" in error_msg.lower():
                print(f"Error fetching data for query (429 Rate Limited): {e}")
            else:
                print(f"Error fetching data for query: {e}")
            return 0.0
