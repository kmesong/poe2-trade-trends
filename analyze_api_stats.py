import requests
import json
import time
import re
import os
from collections import defaultdict
import sys

# Configuration
SEARCH_URL = "https://www.pathofexile.com/api/trade2/search/poe2/Fate%20of%20the%20Vaal"
FETCH_URL_BASE = "https://www.pathofexile.com/api/trade2/fetch/"
OUTPUT_PATH = r"D:\300 Projects\357 POE2 Trades\poe2-trends\public\stats.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Cookie": "POESESSID=a41245dcc7722dca4bffcca666812e58" 
}

SEARCH_PAYLOAD = {
    "query": {
        "status": {"option": "available"},
        "stats": [{"type": "and", "filters": [], "disabled": False}],
        "filters": {
            "misc_filters": {"filters": {"mirrored": {"option": "true"}}, "disabled": False},
            "type_filters": {"filters": {"rarity": {"option": "nonunique"}}, "disabled": False}
        }
    },
    "sort": {"price": "asc"}
}

def normalize_mod(mod_text):
    text = re.sub(r'\d+-\d+', '#-#', mod_text)
    text = re.sub(r'\d+(\.\d+)?', '#', text)
    text = text.replace('+', '').replace('-', '') 
    return text.strip()

def extract_values(mod_text):
    return [float(x) for x in re.findall(r'\d+(?:\.\d+)?', mod_text)]

def get_item_ids():
    print("Fetching item IDs from trade search...")
    try:
        response = requests.post(SEARCH_URL, headers=HEADERS, json=SEARCH_PAYLOAD)
        response.raise_for_status()
        data = response.json()
        
        result_ids = data.get("result", [])
        query_id = data.get("id")
        total = data.get("total")
        
        print(f"Found {total} items. ID: {query_id}")
        return result_ids, query_id
    except requests.exceptions.RequestException as e:
        print(f"Error fetching search results: {e}")
        return [], None

def fetch_item_details(item_ids, query_id):
    items = []
    batch_size = 10
    
    for i in range(0, len(item_ids), batch_size):
        batch = item_ids[i:i + batch_size]
        id_string = ",".join(batch)
        url = f"{FETCH_URL_BASE}{id_string}?query={query_id}&realm=poe2"
        
        print(f"Fetching batch {i//batch_size + 1}/{(len(item_ids) + batch_size - 1)//batch_size}...")
        
        try:
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            data = response.json()
            items.extend(data.get("result", []))
            time.sleep(1) 
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching batch {batch}: {e}")
            
    return items

def analyze_items(items):
    print("\nAnalyzing items...")
    
    # Structure: { "ItemType": { "count": 0, "mods": { (ModText, Type): { "count": 0, "values": [] } } } }
    analysis = defaultdict(lambda: {"count": 0, "mods": defaultdict(lambda: {"count": 0, "values": []})})
    
    for entry in items:
        item = entry.get("item", {})
        base_type = item.get("baseType", "Unknown")
        
        item_category = base_type
        if "Bow" in base_type: item_category = "Bow"
        elif "Wand" in base_type: item_category = "Wand"
        elif "Staff" in base_type: item_category = "Staff"
        elif "Crossbow" in base_type: item_category = "Crossbow"
        elif "Talisman" in base_type: item_category = "Talisman"
        elif "Quiver" in base_type: item_category = "Quiver"
        
        analysis[item_category]["count"] += 1
        
        # Build affix map for this item to help identify P/S
        # Map: normalized_value_tuple -> type (P/S)
        affix_lookup = []
        if "extended" in item and "mods" in item["extended"]:
            for mod_type in ["explicit", "fractured", "desecrated"]:
                if mod_type in item["extended"]["mods"]:
                    for mod_def in item["extended"]["mods"][mod_type]:
                        tier = mod_def.get("tier", "")
                        tier_type = "explicit"
                        if tier.startswith("P"): tier_type = "prefix"
                        elif tier.startswith("S"): tier_type = "suffix"
                        
                        # Store magnitudes to match against text values
                        magnitudes = mod_def.get("magnitudes", [])
                        if magnitudes:
                            # Extract ranges
                            ranges = []
                            for mag in magnitudes:
                                try:
                                    min_v = float(mag.get("min", 0))
                                    max_v = float(mag.get("max", 0))
                                    ranges.append((min_v, max_v))
                                except: pass
                            affix_lookup.append({"type": tier_type, "ranges": ranges, "tier": tier})

        mod_categories = {
            "explicit": item.get("explicitMods", []),
            "implicit": item.get("implicitMods", []),
            "fractured": item.get("fracturedMods", []),
            "rune": item.get("runeMods", []),
            "desecrated": item.get("desecratedMods", [])
        }
        
        seen_mods_for_item = set()
        
        for cat_name, mods in mod_categories.items():
            for mod in mods:
                clean_mod = re.sub(r'\[([^\|\]]+)\|([^\]]+)\]', r'\2', mod)
                clean_mod = re.sub(r'\[([^\]]+)\]', r'\1', clean_mod)
                
                normalized = normalize_mod(clean_mod)
                mod_values = extract_values(clean_mod)
                
                final_type = cat_name
                
                # Refine type
                if cat_name == "rune":
                    if clean_mod.startswith("Bonded") or "Bonded" in clean_mod:
                        final_type = "bonded"
                    else:
                        final_type = "rune" # or 'enchant'
                elif cat_name == "implicit":
                    final_type = "implicit"
                elif cat_name == "fractured":
                    final_type = "fractured"
                elif cat_name in ["explicit", "desecrated"]:
                    # Try to identify P/S
                    # Check if ANY affix range covers ALL values in this mod
                    best_match = "explicit" 
                    
                    if mod_values:
                        for affix in affix_lookup:
                            # Check if all values in mod match a range in affix
                            # Ideally, count of ranges should match count of values? 
                            # Often 1 text line = 1 affix.
                            
                            # Simple check: is the first value in range?
                            if len(mod_values) > 0 and len(affix["ranges"]) > 0:
                                val = mod_values[0]
                                # Check if val fits in ANY range of this affix
                                # (Because order might vary)
                                match = False
                                for (min_v, max_v) in affix["ranges"]:
                                    if min_v <= val <= max_v:
                                        match = True
                                        break
                                
                                if match:
                                    best_match = affix["type"] # prefix/suffix
                                    # Don't break immediately, could be ambiguous? 
                                    # But usually first match is good enough for trend analysis.
                                    break
                    
                    final_type = best_match

                # Key by (text, type) to separate distinct sources (e.g. Implicit vs Explicit)
                unique_key = (normalized, final_type)
                
                if unique_key not in seen_mods_for_item:
                    mod_data = analysis[item_category]["mods"][unique_key]
                    mod_data["count"] += 1
                    mod_data["values"].append(mod_values)
                    
                    seen_mods_for_item.add(unique_key)

    output_data = {}
    
    for w_type, data in analysis.items():
        total_items = data["count"]
        if total_items == 0: continue
            
        stats_list = []
        for (mod_name, mod_type), mod_info in data["mods"].items():
            count = mod_info["count"]
            all_values_lists = mod_info["values"]
            
            stats_per_pos = []
            if all_values_lists:
                max_len = max(len(lst) for lst in all_values_lists)
                for k in range(max_len):
                    vals_at_k = [lst[k] for lst in all_values_lists if k < len(lst)]
                    if vals_at_k:
                        stats_per_pos.append({
                            "min": min(vals_at_k),
                            "max": max(vals_at_k),
                            "avg": round(sum(vals_at_k) / len(vals_at_k), 1)
                        })
                    else:
                        stats_per_pos.append({"min": 0, "max": 0, "avg": 0})
            
            stats_list.append({
                "name": mod_name,
                "type": mod_type,
                "count": count,
                "percentage": round((count / total_items) * 100, 1),
                "values": stats_per_pos
            })
            
        sorted_stats = sorted(stats_list, key=lambda x: x["count"], reverse=True)
        
        output_data[w_type] = {
            "total_items": total_items,
            "stats": sorted_stats
        }

    try:
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"\nSuccess! Dashboard data saved to: {OUTPUT_PATH}")
    except Exception as e:
        print(f"\nError saving JSON: {e}")

def main():
    ids, query_id = get_item_ids()
    if ids:
        item_data = fetch_item_details(ids, query_id)
        analyze_items(item_data)
    else:
        print("No items found to analyze.")

if __name__ == "__main__":
    main()
