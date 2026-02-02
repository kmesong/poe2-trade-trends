## Setup Environment & Test Infrastructure
- Added sys.path modification to backend/conftest.py to ensure backend modules are discoverable by pytest when running from the root.
- Hardcoded currency rates for V1 to ensure functionality without external API.
- Used top 10 results for average price calculation in PriceAnalyzer.
- Normalized everything to Chaos as the base unit.
- Implemented 'item_validator' parameter in '_get_average_price' to allow flexible filtering of search results before averaging.
- Added '_is_t1_magic' helper method to 'PriceAnalyzer' to centralize the Tier 1 check logic.
