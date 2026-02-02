## Setup Environment & Test Infrastructure
- Root .gitignore already handles .env, so no separate backend/.gitignore was created.
Created TradeAPI class to encapsulate PoE trade API interactions.
Used requests-mock for testing API calls and verifying headers like POESESSID.
TradeAPI supports optional session_id for authenticated searches.
- PoE2 trade rarity filters used were 'normal' and 'magic'.
- Mocks were essential for testing the analyzer without hitting the actual PoE API.
- PoE2 Magic items use 'P1'/'S1' notation for Tier 1 modifiers in the 'extended.mods' section of the trade API response.
- 'extended.mods' contains multiple categories (explicit, implicit, fractured, etc.), so iterating over all of them is more robust for filtering.
Updated PriceAnalyzer tests to include T1 mod tiers (P1/S1) in mock data to satisfy the new validation logic.
