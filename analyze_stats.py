import re
import os
from collections import defaultdict

file_path = r"D:\300 Projects\357 POE2 Trades\PoE2 Trade - Path of Exile - Mirrored items.htm"

def normalize_mod(mod_text):
    # Replace numbers with #
    # Handle ranges like 39-65 first
    text = re.sub(r'\d+-\d+', '#-#', mod_text)
    text = re.sub(r'\d+(\.\d+)?', '#', text)
    # Collapse multiple # (e.g. adds # to # -> adds # to #)
    return text.strip()

def analyze_items():
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Naive extraction based on the observation of the page structure from the snapshot.
    # The snapshot suggests a structure. Since I don't have the exact HTML structure, 
    # I will try to rely on the fact that 'result' items usually group these texts.
    # However, parsing raw HTML with regex is fragile. 
    # Let's try to simulate the text extraction logic seen in the snapshot.
    
    # We will split the content by "Verified" which seems to appear for each listed item
    # or look for the "row" class structure if possible. 
    # Let's try splitting by "Verified" as a marker for the start of a trade listing (mostly).
    
    # Actually, the snapshot shows "Verified" -> Name -> Base -> Type -> Stats.
    
    items_raw = content.split('Verified')
    
    weapon_stats = defaultdict(lambda: {"count": 0, "mods": defaultdict(int)})
    
    # Known weapon types to look for
    valid_types = [
        "Bow", "Wand", "Staff", "Two Hand Mace", "Crossbow", 
        "Quarterstaff", "Spear", "Sceptre", "Dagger", "Claw", 
        "One Hand Sword", "Two Hand Sword", "One Hand Axe", 
        "Two Hand Axe", "One Hand Mace", "Fails", "Shield", "Quiver" # Added shields/quivers just in case
    ]

    for item_chunk in items_raw[1:]: # Skip preamble
        # Clean up chunk to remove HTML tags for text analysis
        # This is a very rough text extraction
        clean_text = re.sub(r'<[^>]+>', '\n', item_chunk)
        lines = [line.strip() for line in clean_text.split('\n') if line.strip()]
        
        # Find type
        item_type = None
        for i, line in enumerate(lines[:20]): # Type usually appears early
            if line in valid_types:
                item_type = line
                break
        
        if not item_type:
            continue
            
        weapon_stats[item_type]["count"] += 1
        
        # Find mods
        # Mods usually appear after "Item Level" or requirements
        # We need to distinguish actual mods from properties.
        # Properties usually have a colon, e.g., "Physical Damage: 100-200"
        # Mods usually don't, or they are "Grants Skill: ..."
        
        start_mods = False
        for line in lines:
            # Detect start of mod section (heuristics)
            if "Item Level:" in line or "Requires Level" in line:
                start_mods = True
                continue
            
            if not start_mods:
                continue
                
            # Stop conditions
            if line.startswith("Mirrored"):
                break
            if "b/o" in line or "Price" in line:
                break
            if line in ["Corrupted", "Unidentified"]:
                weapon_stats[item_type]["mods"][line] += 1
                continue

            # Skip properties (heuristic: ends with :)
            if ":" in line and not line.startswith("Grants Skill"):
                continue
                
            # Skip noise
            if line in ["P1", "P2", "P3", "S1", "S2", "S3", "Suffix", "Prefix", "(implicit)"]:
                continue
            
            # Skip variable ranges usually appearing after mods in advanced tooltips
            if line.startswith("{") or line.startswith("("):
                continue

            # It's likely a mod
            norm_mod = normalize_mod(line)
            if len(norm_mod) > 3: # Filter tiny noise
                weapon_stats[item_type]["mods"][norm_mod] += 1

    # Print results
    print("ANALYSIS RESULT")
    print("==================================================")
    
    for w_type, data in weapon_stats.items():
        total = data["count"]
        print(f"\nType: {w_type} (Total items: {total})")
        print("-" * 40)
        
        # Sort by frequency
        sorted_mods = sorted(data["mods"].items(), key=lambda x: x[1], reverse=True)
        
        for mod, count in sorted_mods:
            pct = (count / total) * 100
            if pct >= 10: # Only show significant mods (>10%)
                print(f"{count:2d} ({pct:5.1f}%) | {mod}")

if __name__ == "__main__":
    analyze_items()
