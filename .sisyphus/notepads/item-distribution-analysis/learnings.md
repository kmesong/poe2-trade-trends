## Pattern: Background Job Processing
- Used `ThreadPoolExecutor` to offload long-running trade analysis tasks.
- Used `Job` model to track progress and status for frontend polling.
- Integrated `ItemAnalysis` and `Bucket` models to persist deep-dive distribution data.
- Leveraged `app.app_context()` in background workers to access Flask-dependent resources like database models.

## Schema: Item Distribution
- `ItemAnalysis` stores the overall min/max prices and a list of `Bucket` embedded documents.
- `Bucket` captures price ranges, counts, and attribute frequencies (calculated from a sample of items in that range).
