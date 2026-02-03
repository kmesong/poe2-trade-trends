import sys
import os
# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import requests
import json
import time
import re
from collections import defaultdict

# Load environment variables
load_dotenv()

from backend.price_analyzer import PriceAnalyzer
from backend.database import (
    db, init_db, AnalysisResult, Modifier, ExcludedModifier, CustomCategory,
    save_analysis, get_excluded_mods
)

app = Flask(__name__, static_folder='../../poe2-trends/dist', static_url_path='/')
CORS(app)

# Ensure instance folder exists for SQLite database
os.makedirs('instance', exist_ok=True)

# Database configuration
db_url = os.getenv('DATABASE_URL', '').strip().rstrip('/')
if db_url:
    # Fix protocols for SQLAlchemy compatibility
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    elif db_url.startswith('libsql://'):
        db_url = db_url.replace('libsql://', 'sqlite+libsql://', 1)
    elif db_url.startswith('https://'):
        db_url = db_url.replace('https://', 'sqlite+libsql://', 1)
else:
    db_url = 'sqlite:///poe2_trade.db'

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database and create tables
init_db(app)
with app.app_context():
    db.create_all()
@app.route('/')
def index():
    try:
        return app.send_static_file('index.html')
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/<path:path>')
def static_proxy(path):
    try:
        return app.send_static_file(path)
    except Exception:
        return app.send_static_file('index.html')

# Configuration
SEARCH_URL_BASE = "https://www.pathofexile.com/api/trade2/search/poe2/"
FETCH_URL_BASE = "https://www.pathofexile.com/api/trade2/fetch/"
HISTORY_DIR = "saved_data"

def get_session_id():
    """Extract session ID from header or environment."""
    return request.headers.get("X-POESESSID") or os.getenv("POESESSID")

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

@app.route('/analyze/batch-price', methods=['POST'])
def batch_price_analysis():
    session_id = get_session_id()
    if not session_id:
        return jsonify({"error": "Session ID required (X-POESESSID header or POESESSID env)"}), 401
    
    data = request.json
    if not data:
        return jsonify({"error": "No JSON payload provided"}), 400
        
    bases = data.get("bases", [])
    if not bases:
        return jsonify({"error": "No bases provided"}), 400
    
    # Get active exclusions
    exclusions = get_excluded_mods()
    
    analyzer = PriceAnalyzer()
    results = []
    for base in bases:
        print(f"Analyzing {base}...")
        try:
            # Use save_analysis to run analysis AND save to DB
            analysis = save_analysis(
                analyzer=analyzer,
                base_type=base,
                session_id=session_id,
                excluded_mods=exclusions
            )
        except Exception as e:
            print(f"Error analyzing {base}: {e}")
            results.append({"base_type": base, "error": str(e)})
            continue

        results.append(analysis.to_dict())
        time.sleep(2) # Rate limit
        
    return jsonify(results)

# Currency rates endpoint - fetch from poe.ninja
@app.route('/api/currency/rates', methods=['GET'])
def get_currency_rates():
    """
    Get current currency exchange rates.
    Returns rates normalized to Exalted Orbs.
    """
    from backend.currency_service import CurrencyService
    service = CurrencyService()
    return jsonify(service.get_rates())

@app.route('/api/currency/rates', methods=['POST'])
def refresh_currency_rates():
    """
    Refresh currency rates from poe.ninja.
    POST body: {"rates": {"exalted": 1.0, "divine": 0.5, ...}}
    Returns updated rates.
    """
    from backend.currency_service import CurrencyService
    try:
        data = request.get_json()
        if data and "rates" in data:
            service = CurrencyService()
            success = service.refresh_from_poe_ninja(data["rates"])
            if success:
                return jsonify({"success": True, "rates": service.get_rates()})
            else:
                return jsonify({"success": False, "error": "Invalid rates format"}), 400
        else:
            # If no rates provided, just return current rates
            service = CurrencyService()
            return jsonify({"success": True, "rates": service.get_rates()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Items endpoint - proxy to PoE trade API to get item list
@app.route('/api/items', methods=['GET'])
def get_items():
    """
    Fetch item list from PoE trade API.
    Returns categorized items for the batch analysis tree selector.
    """
    try:
        response = requests.get(
            "https://www.pathofexile.com/api/trade2/data/items",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0",
                "Accept": "*/*",
                "X-Requested-With": "XMLHttpRequest"
            },
            timeout=30
        )
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": f"Failed to fetch items: {response.status_code}"}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============== Database API Endpoints ==============

@app.route('/api/db/analyses', methods=['GET'])
def get_analyses():
    """
    Get all saved analysis results.
    Query params:
        - base_type: Filter by item type
        - limit: Maximum results (default 100)
        - latest_only: If true, returns only the latest analysis per base_type
    """
    try:
        base_type = request.args.get('base_type')
        limit = int(request.args.get('limit', 100))
        latest_only = request.args.get('latest_only', 'false').lower() == 'true'

        from backend.database import get_analyses, get_latest_analyses
        
        if latest_only and not base_type:
            analyses = get_latest_analyses(limit=limit)
        else:
            analyses = get_analyses(base_type=base_type, limit=limit)

        return jsonify({
            'success': True,
            'data': [a.to_dict() for a in analyses],
            'count': len(analyses)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/db/analyses/<int:analysis_id>', methods=['GET'])
def get_analysis(analysis_id):
    """
    Get a specific analysis result by ID.
    """
    try:
        from backend.database import AnalysisResult
        analysis = AnalysisResult.query.get_or_404(analysis_id)

        return jsonify({
            'success': True,
            'data': analysis.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/db/exclusions', methods=['GET'])
def get_exclusions():
    """
    Get all active excluded modifier rules.
    """
    try:
        from backend.database import get_excluded_mods
        exclusions = get_excluded_mods()

        return jsonify({
            'success': True,
            'data': [e.to_dict() for e in exclusions],
            'count': len(exclusions)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/db/exclusions', methods=['POST'])
def add_exclusion():
    """
    Add a new excluded modifier rule.

    Body:
        - mod_name_pattern: SQL LIKE pattern (optional)
        - mod_tier: Specific tier like "P1" (optional)
        - mod_type: explicit/implicit/etc (optional)
        - reason: Explanation (optional)
    """
    try:
        data = request.json or {}

        from backend.database import add_excluded_mod

        exclusion = add_excluded_mod(
            name_pattern=data.get('mod_name_pattern'),
            tier=data.get('mod_tier'),
            mod_type=data.get('mod_type'),
            reason=data.get('reason')
        )

        return jsonify({
            'success': True,
            'data': exclusion.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/db/exclusions/<int:exclusion_id>', methods=['DELETE'])
def remove_exclusion(exclusion_id):
    """
    Remove (deactivate) an excluded modifier rule.
    """
    try:
        from backend.database import remove_excluded_mod

        success = remove_excluded_mod(exclusion_id)

        if success:
            return jsonify({'success': True, 'message': 'Exclusion removed'})
        else:
            return jsonify({'success': False, 'error': 'Exclusion not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/db/exclusions/<int:exclusion_id>', methods=['PUT'])
def update_exclusion(exclusion_id):
    """
    Update an excluded modifier rule.
    """
    try:
        from backend.database import ExcludedModifier

        exclusion = ExcludedModifier.query.get_or_404(exclusion_id)
        data = request.json or {}

        if 'mod_name_pattern' in data:
            exclusion.mod_name_pattern = data['mod_name_pattern']
        if 'mod_tier' in data:
            exclusion.mod_tier = data['mod_tier']
        if 'mod_type' in data:
            exclusion.mod_type = data['mod_type']
        if 'reason' in data:
            exclusion.reason = data['reason']
        if 'is_active' in data:
            exclusion.is_active = data['is_active']

        db.session.commit()

        return jsonify({
            'success': True,
            'data': exclusion.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============== Custom Category API Endpoints ==============

@app.route('/api/db/custom-categories', methods=['GET'])
def get_custom_categories():
    """
    Get all user-defined custom categories.
    """
    try:
        categories = CustomCategory.query.all()
        return jsonify({
            'success': True,
            'data': [c.to_dict() for c in categories],
            'count': len(categories)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/db/custom-categories', methods=['POST'])
def create_custom_category():
    """
    Create a new custom category.
    Body:
        - name: Name of the category (unique)
        - items: List of item base names
    """
    try:
        data = request.json or {}
        name = data.get('name')
        items_list = data.get('items', [])

        if not name:
            return jsonify({'success': False, 'error': 'Name is required'}), 400

        # Convert list to comma-separated string
        items_str = ','.join([str(i).strip() for i in items_list])

        category = CustomCategory(name=name, items=items_str)
        db.session.add(category)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': category.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/db/custom-categories/<int:category_id>', methods=['DELETE'])
def delete_custom_category(category_id):
    """
    Delete a custom category by ID.
    """
    try:
        category = CustomCategory.query.get_or_404(category_id)
        db.session.delete(category)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Category deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    print("Starting server on port 5000...")
    app.run(debug=True, port=5000)
