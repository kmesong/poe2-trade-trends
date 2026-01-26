import re
import os
import sys
from collections import defaultdict
from html.parser import HTMLParser

sys.stdout.reconfigure(encoding='utf-8')

file_path = r"D:\300 Projects\357 POE2 Trades\PoE2 Trade - Path of Exile - Mirrored items.htm"

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
    
    def handle_data(self, data):
        cleaned = data.strip()
        if cleaned:
            self.text_parts.append(cleaned)

def normalize_mod(mod_text):
    text = re.sub(r'\d+-\d+', '#-#', mod_text)
    text = re.sub(r'\d+(\.\d+)?', '#', text)
    text = text.replace('+', '').replace('-', '') 
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
    
    weapon_stats = defaultdict(lambda: {"count": 0, "mods": defaultdict(int)})
    
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

        for i, line in enumerate(lines):
            if "Item Level:" in line or "Requires" in line or "Level" == line:
                start_mods = True
                if "Item Level:" in line: 
                    continue 

            if not start_mods:
                continue
                
            if line.startswith("Mirrored") or line.startswith("~b/o") or line.startswith("Asking Price") or "listed" in line.lower():
                break

            if ":" in line and not line.startswith("Grants Skill") and not line.startswith("Bonded"):
                continue
                
            if len(line) < 4:
                continue

            if any(x in line for x in ["(enchant)", "(implicit)", "(crafted)"]):
               line = line.replace("(enchant)", "").replace("(implicit)", "").replace("(crafted)", "").strip()

            is_ignored = False
            for ignore in ignored_lines:
                if line == ignore or line.startswith(ignore + ":"):
                    is_ignored = True
                    break
            
            if is_ignored:
                continue

            norm_mod = normalize_mod(line)
            
            if norm_mod not in seen_mods:
                weapon_stats[item_type]["mods"][norm_mod] += 1
                seen_mods.add(norm_mod)

    print("ANALYSIS RESULT")
    print("==================================================")
    
    sorted_types = sorted(weapon_stats.keys())

    for w_type in sorted_types:
        data = weapon_stats[w_type]
        total = data["count"]
        print(f"\nType: {w_type} (Total items: {total})")
        print("-" * 40)
        
        sorted_mods = sorted(data["mods"].items(), key=lambda x: x[1], reverse=True)
        
        for mod, count in sorted_mods:
            pct = (count / total) * 100
            if pct >= 5 and count > 1: 
                print(f"{count:2d} ({pct:5.1f}%) | {mod}")

if __name__ == "__main__":
    analyze_items()
