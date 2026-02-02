Successfully updated PriceAnalyzer.analyze_gap to include an ilvl filter (min: 81) in the magic_query. This ensures that the search is more targeted towards high-tier modifiers. The client-side _is_t1_magic check was preserved as requested.

- Implemented a batched fetching mechanism in `_get_average_price` to get more accurate average prices by looking deeper into search results (up to 50 items) when initial results are filtered out.
- Used `time.sleep(0.5)` to respect API polite usage guidelines between batches.
- Leveraged `unittest.mock.patch` to mock `time.sleep` in tests to avoid slowing down the test suite.
- Added `test_get_average_price_recursive` to verify that the logic correctly fetches subsequent batches when items in the first batch fail validation.
