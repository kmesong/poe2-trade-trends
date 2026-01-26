import re
import os
import sys
import json
from collections import defaultdict
from html.parser import HTMLParser

sys.stdout.reconfigure(encoding='utf-8')

file_path = r"D:\300 Projects\357 POE2 Trades\PoE2 Trade - Path of Exile - Mirrored items.htm"
output_path = r"D:\300 Projects\357 POE2 Trades\poe2-trends\public\stats.json"

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.rune_div_depth = 0
    
    def handle_starttag(self, tag, attrs):
        if tag == 'div':
            is_rune = False
            for name, value in attrs:
                if name == 'class' and 'runeMod' in value:
                    is_rune = True
                    break
            
            if is_rune:
                # If we were already in a rune mod (nested runeMod?), reset depth to 1 or add?
                # Assuming runeMods are not nested inside runeMods usually.
                # If they are, this logic resets the counter which is fine as long as > 0
                self.rune_div_depth = 1 
            elif self.rune_div_depth > 0:
                self.rune_div_depth += 1

    def handle_endtag(self, tag):
        if tag == 'div':
            if self.rune_div_depth > 0:
                self.rune_div_depth -= 1
            
    def handle_data(self, data):
        cleaned = data.strip()
        if cleaned:
            # Prefix with a marker if it's a rune mod
            if self.rune_div_depth > 0:
                self.text_parts.append(f"__RUNE_MARKER__{cleaned}")
            else:
                self.text_parts.append(cleaned)



def normalize_mod(mod_text):
    text = re.sub(r'\d+(?:\.\d+)?', '#', mod_text)
    
    if text.startswith('+'):
        text = text[1:]
        
    return text.strip()


def analyze_items():
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    parser = TextExtractor()
    parser.feed(content)
    all_text = parser.text_parts

    items_text_blob = "\n".join(all_text)
    items_raw = items_text_blob.split('Verified')
    
    weapon_stats = defaultdict(lambda: {"count": 0, "mods": defaultdict(lambda: {"count": 0, "values": []})})


    
    valid_types = [
        "Bow", "Wand", "Staff", "Two Hand Mace", "Crossbow", 
        "Quarterstaff", "Spear", "Sceptre", "Dagger", "Claw", 
        "One Hand Sword", "Two Hand Sword", "One Hand Axe", 
        "Two Hand Axe", "One Hand Mace", "Shield", "Quiver", "Amulet", "Ring", "Belt", "Talisman"
    ]

    ignored_lines = {
        "P1", "P2", "P3", "S1", "S2", "S3", "Suffix", "Prefix", "(implicit)",
        "Any", "Yes", "No", "Level", "Strength", "Dexterity", "Intelligence",
        "Corrupted", "Mirrored", "Unidentified", "Fractured", "Synthesised",
        "Item Level", "Quality", "Physical Damage", "Elemental Damage", 
        "Critical Hit Chance", "Attacks per Second", "Reload Time", "Energy Shield",
        "Armour", "Evasion Rating", "Block", "Spirit", "Augmentable Sockets",
        "Requirements", "Price", "Seller", "Listed", "Contact Options",
        "Travel to Hideout", "Ignore Player", "Pin", "Unpin", "Copy Whisper",
        "Direct Whisper", "Default", "Compact", "Compact Two-Columned", 
        "Back to Top", "Search Listed Items", "Bulk Item Exchange", "About",
        "Settings", "History", "Sign In", "Home", "Trade"
    }

    for item_chunk in items_raw[1:]:
        lines = [line.strip() for line in item_chunk.split('\n') if line.strip()]
        
        item_type = None
        for line in lines[:30]:
            if line in valid_types:
                item_type = line
                break
        
        if not item_type:
            continue
            
        weapon_stats[item_type]["count"] += 1
        
        start_mods = False
        seen_mods = set()

        i = 0
        while i < len(lines):
            line = lines[i]

            if "Item Level:" in line or "Requires" in line or "Level" == line:
                start_mods = True
                if "Item Level:" in line:
                    i += 1
                    continue 

            if not start_mods:
                i += 1
                continue
                
            if line.startswith("Mirrored") or line.startswith("~b/o") or line.startswith("Asking Price") or "listed" in line.lower():
                break
            
            # 0. Filter out base property ranges (e.g. [100-200])
            if line.startswith("[") and (line.endswith("]") or "to" in line):
                i += 1
                continue
                
            # Handle RUNE MARKER early
            is_marked_rune = False
            if line.startswith("__RUNE_MARKER__"):
                is_marked_rune = True
                line = line.replace("__RUNE_MARKER__", "")

            if "≥" in line or line.startswith("of ") or line.endswith(")") or "Runic" in line or "Frostbound" in line or "Stormbound" in line or "Flamebound" in line:

                # These are usually modifier names/tiers (e.g. "of the Wizard (≥78)", "Frostbound (≥80)")
                # We want to SKIP these lines, they are NOT stats.
                # Heuristic: ends with (≥#) and is short, or starts with "of "
                if re.search(r'\(\u2265\d+\)', line): # Matches (≥number)
                     i += 1
                     continue
            
            # Check for split lines BEFORE filtering


            # 1. Grants Skill:
            if line == "Grants Skill:" and i + 1 < len(lines):
                line = f"{line} {lines[i+1]}"
                i += 1 

            # 2. Ends with "gain an" or "to" (common split points)
            elif (line.endswith(" gain an") or line.endswith(" to")) and i + 1 < len(lines):
                line = f"{line} {lines[i+1]}"
                i += 1

            # 3. Handle Requires split (e.g. "Requires Level 60", ", 100 Str")
            if line.startswith("Requires"):
                 while i + 1 < len(lines):
                    next_line = lines[i+1]
                    # Heuristic: Requirement parts usually contain specific keywords or start with punctuation/numbers
                    is_req_part = (
                        next_line.startswith(",") or 
                        next_line.startswith("Level") or 
                        "Str" in next_line or "Dex" in next_line or "Int" in next_line or 
                        re.match(r'^[\d\s,]+$', next_line) # Just numbers/commas
                    )
                    
                    if is_req_part:
                        line = f"{line}{next_line}" if next_line.startswith(",") else f"{line} {next_line}"
                        i += 1
                    else:
                        break


            if ":" in line and not line.startswith("Grants Skill") and not line.startswith("Bonded"):

                i += 1
                continue
                
            if len(line) < 4:
                i += 1
                continue

            # Determine Type based on ORIGINAL line content (before replacement)
            # Default to explicit
            mod_type = "explicit"
            
            # User request: "for bonded stats, if it does not start with Bonded, it is a rune"
            if line.startswith("Bonded"):
                mod_type = "bonded"
            elif is_marked_rune or "(enchant)" in line:
                mod_type = "rune"
            elif "(implicit)" in line or line.startswith("Grants Skill"):
                mod_type = "implicit"





            if any(x in line for x in ["(enchant)", "(implicit)", "(crafted)"]):
               line = line.replace("(enchant)", "").replace("(implicit)", "").replace("(crafted)", "").strip()


            is_ignored = False
            for ignore in ignored_lines:
                if line == ignore or line.startswith(ignore + ":"):
                    is_ignored = True
                    break
            
            if is_ignored:
                i += 1
                continue

            norm_mod = normalize_mod(line)
            
            if norm_mod not in seen_mods:
                numbers = [float(x) for x in re.findall(r'\d+(?:\.\d+)?', line)]
                
                weapon_stats[item_type]["mods"][norm_mod]["values"].append(numbers)
                weapon_stats[item_type]["mods"][norm_mod]["count"] += 1
                
                # Only set type if not already set (or prioritize specific types if seen differently)
                # But typically a mod is consistent.
                weapon_stats[item_type]["mods"][norm_mod]["type"] = mod_type
                
                seen_mods.add(norm_mod)

            
            i += 1

    output_data = {}
    for w_type, data in weapon_stats.items():
        stats_list = []
        for mod_name, mod_data in data["mods"].items():
            count = mod_data["count"]
            all_values_lists = mod_data["values"]
            mod_type = mod_data["type"]
            
            if not all_values_lists:

                stats_per_pos = []
            else:
                max_len = max(len(lst) for lst in all_values_lists)
                stats_per_pos = []
                
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

            stat_entry = {
                "name": mod_name,
                "type": mod_type,
                "count": count,
                "percentage": round((count / data["count"]) * 100, 1),
                "values": stats_per_pos 
            }

            stats_list.append(stat_entry)

        sorted_mods = sorted(stats_list, key=lambda x: x["count"], reverse=True)
        
        output_data[w_type] = {
            "total_items": data["count"],
            "stats": sorted_mods
        }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
        
    print(f"JSON data saved to {output_path}")

if __name__ == "__main__":
    analyze_items()
