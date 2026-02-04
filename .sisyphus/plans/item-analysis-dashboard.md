# Item Analysis Dashboard

## Context

### Original Request
Add functionality to analyze a "particular item" by:
1. Finding Lowest (avg 5) and Highest (avg 5) prices.
2. Creating 10 price buckets between Low and High.
3. Running analysis for *every bucket* (fetching items in that range).
4. Recording "every attribute" (specs) to see what influences price.
5. Visualizing results on a dashboard.
6. Saving data for future reference.

### Interview Summary
**Key Discussions**:
- **Input**: Reuse `ItemTree` for selection (Base Type).
- **Scope**: "Every attribute" includes mods, ilvl, quality, sockets, links, corruption, etc.
- **Logic**: Top/Bottom 20% comparison + Linear price buckets.
- **Viz**: Recharts approved.
- **Persistence**: Save results to MongoDB.

**Research Findings**:
- **Backend**: Python Flask + MongoDB (mongoengine). `Job` system exists and is required for this heavy task.
- **Rate Limits**: 10 buckets + 2 range checks = 12+ API calls. STRICT serial execution required (sleep 2s between calls). Total time ~30-60s per analysis.
- **Frontend**: React/Vite. No chart lib yet.

### Metis Review
**Identified Gaps** (addressed):
- **Empty Buckets**: If no items found in a bucket, record 0 count but don't fail job.
- **Outliers**: If High >> Low (e.g. 1 mirror vs 1 divine), linear buckets will be sparse. *Decision: Stick to linear as requested, but log warning.*
- **Rate Limit Safety**: Must enforce 2s sleep between bucket queries.

---

## Work Objectives

### Core Objective
Build a "Deep Dive" analysis tool that segments items by price to reveal correlation between attributes and value.

### Concrete Deliverables
- **Backend**: `POST /api/analyze/distribution` (starts Job).
- **Database**: `ItemAnalysis` model (stores bucketed data).
- **Frontend**: `/item-analysis` page with Recharts histogram and "Influence" table.

### Definition of Done
- [ ] User can select "Vaal Axe" -> System runs ~1 min analysis.
- [ ] Dashboard shows histogram of prices (10 bars).
- [ ] Clicking a bar shows stats for that price range.
- [ ] "Influence" table shows which mods appear more in high buckets vs low buckets.
- [ ] Results persist in History.

### Must Have
- **Job System Integration**: Long-running tasks must be async.
- **Rate Limit Safety**: 2s delay between GGG API calls.
- **Persistence**: Save results to DB.

### Must NOT Have (Guardrails)
- **Parallel API Calls**: NEVER run bucket queries in parallel (instant IP ban).
- **Infinite Retries**: Fail job if >3 buckets fail.

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES (pytest).
- **User wants tests**: YES (implied by "robustness").
- **Strategy**: **Manual Verification + Unit Tests for Logic**.
  - **Logic**: Test bucket calculation and attribute extraction (no API calls).
  - **Integration**: Manual test with "Tabula Rasa" (common item) and "Vaal Axe" (rare).

### Manual QA Procedure

**Backend Logic**:
- [ ] Unit test: `test_price_analyzer.py:test_bucket_calculation` (given min 10, max 110, steps 10 -> verifies ranges).
- [ ] Unit test: `test_analysis.py:test_attribute_extraction` (given raw item JSON -> verifies all fields extracted).

**End-to-End**:
1. Open Dashboard -> `/item-analysis`.
2. Select "Tabula Rasa" (or common unique/base).
3. Click "Analyze".
4. Verify Job starts (Status: "Processing").
5. Monitor logs: Ensure ~2s delay between "Fetching bucket X..." messages.
6. Wait for completion.
7. Verify Charts appear.
8. Refresh page -> Verify History loads.

---

## Task Flow

```
1. Backend: DB Models & Logic  -> 2. Backend: API & Job  -> 3. Frontend: Recharts & UI
```

---

## TODOs

- [x] 1. Create `ItemAnalysis` MongoDB Model
  **What to do**:
  - Create `backend/database.py:ItemAnalysis` class.
  - Fields: `base_type`, `timestamp`, `min_price`, `max_price`, `buckets` (List of Dicts).
  - `Bucket` structure: `price_range` (str), `count` (int), `avg_price` (float), `attributes` (Dict).
  - Add to `init_db`.
  
  **References**:
  - `backend/database.py:SearchHistory` - Follow similar pattern.

  **Acceptance Criteria**:
  - [ ] Model importable in shell.
  - [ ] Can save/load dummy data.

- [x] 2. Implement `PriceAnalyzer.analyze_distribution` (Logic Only)
  **What to do**:
  - Update `backend/price_analyzer.py`.
  - Add `analyze_distribution(base_type, buckets=10)`.
  - Logic:
    1. `_get_price_range`: Fetch Sort ASC (Low) and Sort DESC (High). Avg top 5.
    2. Calculate steps.
    3. Loop 10 times: Build query with `price.min` and `price.max`.
    4. Call `_get_search_result` -> `_calculate_average`.
    5. **CRITICAL**: `time.sleep(2)` inside loop.
  - Add `_extract_attributes(item)`: Extract `ilvl`, `sockets` (count), `links` (max), `corrupted`, `quality`, `scourged`, etc.

  **References**:
  - `backend/price_analyzer.py:analyze_gap` - Reuse search pattern.
  - `backend/trade_api.py:search` - Use existing client.

  **Acceptance Criteria**:
  - [ ] `pytest backend/tests/test_price_analyzer.py` passes (mocked API).
  - [ ] `_extract_attributes` captures non-mod stats correctly.

- [x] 3. Create Backend Job & Endpoint
  **What to do**:
  - Update `backend/server.py`.
  - Endpoint: `POST /api/analyze/distribution` -> Creates `Job`.
  - Worker: `process_distribution_analysis(job_id, base_type)`.
  - Calls `analyzer.analyze_distribution`.
  - Saves result to `ItemAnalysis` and updates `Job`.

  **References**:
  - `backend/server.py:create_batch_job` - Reuse pattern.

  **Acceptance Criteria**:
  - [ ] `curl -X POST /api/analyze/distribution` returns job ID.
  - [ ] Job status updates from `queued` -> `processing` -> `completed`.

- [x] 4. Frontend: Setup & Recharts
  **What to do**:
  - `cd poe2-trends && npm install recharts`.
  - Create `src/types.ts`: Add `ItemAnalysisResult` interface.
  - Create `src/services/analysis.ts`: Add `startDistributionAnalysis`, `getAnalysisHistory`.

  **Acceptance Criteria**:
  - [ ] Recharts installed.
  - [ ] Types compile.

- [x] 5. Frontend: Item Analysis Page
  **What to do**:
  - Create `src/pages/ItemAnalysis.tsx`.
  - Reuse `Sidebar` and `ItemTree` (maybe extract Tree to component if not already).
  - Layout:
    - Top: Item Selector + "Analyze" Button.
    - Middle: Progress Bar (if job running).
    - Bottom:
      - Left: Price Histogram (Recharts `BarChart`).
      - Right: "Influence" Table (List attributes with biggest diff between Low/High buckets).

  **Acceptance Criteria**:
  - [ ] Page loadable via `/item-analysis`.
  - [ ] Can select item and start job.
  - [ ] Charts render dummy data.

- [x] 6. Frontend: Connect & Visualize
  **What to do**:
  - Hook up API calls in `ItemAnalysis.tsx`.
  - Polling for Job status.
  - On complete: Fetch result and render.
  - Implement "Influence" logic in frontend:
    - Compare `bucket[0]` (Low) vs `bucket[9]` (High).
    - If `mod X` freq is 10% in Low and 90% in High -> Show as "High Value".

  **Acceptance Criteria**:
  - [ ] Full end-to-end flow works.
  - [ ] "Influence" table shows logical results (e.g. "6 links" correlates with high price).

---

## Success Criteria

### Verification Commands
```bash
# Backend Logic Test
pytest backend/tests/test_price_analyzer.py

# End-to-End
curl -X POST http://localhost:5000/api/analyze/distribution -H "Content-Type: application/json" -d '{"base_type": "Vaal Axe"}'
```

### Final Checklist
- [ ] 10 Price Buckets generated.
- [ ] Analysis runs without hitting 429 (Rate Limit).
- [ ] Data persists in MongoDB.
- [ ] Dashboard visualizes Price vs Attribute frequency.
