from html.parser import HTMLParser

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
    
    def handle_data(self, data):
        cleaned = data.strip()
        if cleaned.startswith('[') and '—' in cleaned:
            print(f"Found: {cleaned}")

with open(r"D:\300 Projects\357 POE2 Trades\PoE2 Trade - Path of Exile - Mirrored items.htm", 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()
    parser = TextExtractor()
    parser.feed(content)
