from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import time
import re
import os
from collections import defaultdict
import sys

app = Flask(__name__, static_folder='../poe2-trends/dist', static_url_path='/')
CORS(app)  # Enable CORS for all routes

# Serve React App
@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/<path:path>')
def static_proxy(path):
    # send_static_file will guess the correct MIME type
    try:
        return app.send_static_file(path)
    except:
        # If file not found, fall back to index.html for client-side routing
        return app.send_static_file('index.html')

# Configuration
SEARCH_URL_BASE = "https://www.pathofexile.com/api/trade2/search/poe2/"
FETCH_URL_BASE = "https://www.pathofexile.com/api/trade2/fetch/"
HISTORY_DIR = "saved_data"

if not os.path.exists(HISTORY_DIR):
    os.makedirs(HISTORY_DIR)

# Default Headers (User-Agent is critical)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Cookie": "POESESSID=a41245dcc7722dca4bffcca666812e58" # Ideally this comes from request or is updated
}

def normalize_mod(mod_text):
    text = re.sub(r'\d+-\d+', '#-#', mod_text)
    text = re.sub(r'\d+(\.\d+)?', '#', text)
    text = text.replace('+', '').replace('-', '') 
    return text.strip()

def extract_values(mod_text):
    return [float(x) for x in re.findall(r'\d+(?:\.\d+)?', mod_text)]

def analyze_items_logic(items):
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
        
        # Build affix map
        affix_lookup = []
        if "extended" in item and "mods" in item["extended"]:
            for mod_type in ["explicit", "fractured", "desecrated"]:
                if mod_type in item["extended"]["mods"]:
                    for mod_def in item["extended"]["mods"][mod_type]:
                        tier = mod_def.get("tier", "")
                        tier_type = "explicit"
                        if tier.startswith("P"): tier_type = "prefix"
                        elif tier.startswith("S"): tier_type = "suffix"
                        
                        magnitudes = mod_def.get("magnitudes", [])
                        if magnitudes:
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
                
                if cat_name == "rune":
                    if clean_mod.startswith("Bonded") or "Bonded" in clean_mod:
                        final_type = "bonded"
                    else:
                        final_type = "rune" 
                elif cat_name == "implicit":
                    final_type = "implicit"
                elif cat_name == "fractured":
                    final_type = "fractured"
                elif cat_name in ["explicit", "desecrated"]:
                    best_match = "explicit" 
                    if mod_values:
                        for affix in affix_lookup:
                            if len(mod_values) > 0 and len(affix["ranges"]) > 0:
                                val = mod_values[0]
                                match = False
                                for (min_v, max_v) in affix["ranges"]:
                                    if min_v <= val <= max_v:
                                        match = True
                                        break
                                if match:
                                    best_match = affix["type"]
                                    break
                    final_type = best_match

                unique_key = (normalized, final_type)
                if unique_key not in seen_mods_for_item:
                    mod_data = analysis[item_category]["mods"][unique_key]
                    mod_data["count"] += 1
                    mod_data["values"].append(mod_values)
                    seen_mods_for_item.add(unique_key)

    # Format Output
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
        
    return output_data

@app.route('/history', methods=['GET'])
def list_history():
    files = []
    if os.path.exists(HISTORY_DIR):
        for f in os.listdir(HISTORY_DIR):
            if f.endswith(".json"):
                path = os.path.join(HISTORY_DIR, f)
                try:
                    with open(path, 'r', encoding='utf-8') as file:
                        meta = json.load(file)
                        files.append({
                            "filename": f,
                            "name": meta.get("name", f),
                            "date": meta.get("date"),
                            "timestamp": meta.get("timestamp", 0)
                        })
                except: pass
    
    files.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return jsonify(files)

@app.route('/history/<filename>', methods=['GET'])
def get_history_item(filename):
    if not filename.endswith('.json') or '/' in filename or '\\' in filename:
        return jsonify({"error": "Invalid filename"}), 400
        
    path = os.path.join(HISTORY_DIR, filename)
    if not os.path.exists(path):
        return jsonify({"error": "File not found"}), 404
        
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return jsonify(data.get("results", {}))

@app.route('/save', methods=['POST'])
def save_history():
    data = request.json
    name = data.get("name")
    results = data.get("results")
    query = data.get("query")
    
    if not name or not results:
        return jsonify({"error": "Missing name or results"}), 400
    
    timestamp = int(time.time())
    date_str = time.strftime("%Y-%m-%d %H:%M:%S")
    
    # Sanitize name
    safe_name = re.sub(r'[^a-zA-Z0-9_\- ]', '', name).strip().replace(' ', '_')
    filename = f"{timestamp}_{safe_name}.json"
    
    save_data = {
        "name": name,
        "date": date_str,
        "timestamp": timestamp,
        "query": query,
        "results": results
    }
    
    path = os.path.join(HISTORY_DIR, filename)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f)
        return jsonify({"success": True, "filename": filename, "date": date_str, "timestamp": timestamp})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON payload provided"}), 400
            
        league = data.get("league", "Fate of the Vaal")
        query_text = data.get("query_text", "")
        
        # Parse query input
        # It could be:
        # 1. A JSON object string
        # 2. A cURL command (harder, but common)
        # 3. Just the "query" part of the JSON
        
        try:
            # Try to parse as JSON
            parsed = json.loads(query_text)
            
            # If it has "query" key at root, use it directly
            if "query" in parsed:
                query_payload = parsed["query"]
            else:
                # Assume the whole thing is the query payload
                query_payload = parsed
                
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON format. Please paste a valid PoE Trade query JSON."}), 400
        
        # Determine Search URL based on league
        # Defaulting to poe2/LeagueName
        search_url = f"{SEARCH_URL_BASE}{league}"
        
        print(f"Executing search on {search_url}...")
        
        # 1. Execute Search
        response = requests.post(search_url, headers=HEADERS, json={"query": query_payload, "sort": {"price": "asc"}})
        response.raise_for_status()
        search_result = response.json()
        
        result_ids = search_result.get("result", [])
        query_id = search_result.get("id")
        
        if not result_ids:
            return jsonify({"error": "No items found for this query", "raw": search_result}), 404
            
        # 2. Fetch Details (Limit to 100 to avoid long waits/bans)
        LIMIT = 100
        items_to_fetch = result_ids[:LIMIT]
        all_items = []
        
        batch_size = 10
        for i in range(0, len(items_to_fetch), batch_size):
            batch = items_to_fetch[i:i + batch_size]
            id_string = ",".join(batch)
            fetch_url = f"{FETCH_URL_BASE}{id_string}?query={query_id}&realm=poe2"
            
            print(f"Fetching batch {i}...")
            r = requests.get(fetch_url, headers=HEADERS)
            if r.status_code == 200:
                all_items.extend(r.json().get("result", []))
            time.sleep(0.5) # Politeness delay
            
        # 3. Analyze
        analysis_result = analyze_items_logic(all_items)
        
        return jsonify(analysis_result)

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting server on port 5000...")
    app.run(debug=True, port=5000)
