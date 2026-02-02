# Error Handling & Toast Notifications

## Context

### Original Request
User wants to distinguish 429 (rate limit) vs 502 (server error) errors with real-time toast notifications in the UI.

### Interview Summary

**Key Discussions**:
- Toast notifications via `react-hot-toast` library
- TDD approach (tests first)
- Different retry strategies for 429 vs 502
- Backend needs better error logging
- Frontend needs error events from backend for toasts

**Research Findings**:
- `trade_api.py` only handles 429, not 502
- `price_analyzer.py` catches all exceptions silently
- User has pytest infrastructure with existing 429 tests
- Server delays may be too aggressive (0.5s, 2s)

### Metis Review

**Identified Gaps**:
- Backend-to-frontend error communication needs design decision (SSE vs polling vs simple error response)
- Need to decide: should retry attempts trigger individual toasts or just final result?
- Graceful degradation: what happens if all retries fail?

---

## Work Objectives

### Core Objective
Distinguish and properly handle 429 (rate limit) vs 502 (server error) with real-time toast notifications in the UI.

### Concrete Deliverables
- Updated `trade_api.py` with 502 retry logic
- Better error logging in backend
- Toast notifications in frontend via `react-hot-toast`
- Error events passed from backend to frontend

### Definition of Done
- [ ] 502 errors are retried with exponential backoff
- [ ] Console clearly shows which error type occurred (429 vs 502)
- [ ] Toast appears on 429: "Rate limited - waiting..."
- [ ] Toast appears on 502: "Server busy - retrying..."
- [ ] All existing tests pass

### Must Have
- 502 error handling with retries
- Clear distinction between 429 and 502 in logs
- Toast notifications for error/retry states

### Must NOT Have (Guardrails)
- No changes to currency service
- No changes to `analyze_gap()` logic
- No modifications to `batch_price_analysis()` except error handling
- No new backend routes (use existing endpoints)

---

## Verification Strategy (TDD)

### Test Decision
- **Infrastructure exists**: YES (pytest)
- **User wants tests**: TDD (tests first)
- **Framework**: pytest

### TDD Workflow
1. Write failing tests for 502 handling
2. Write failing tests for error logging
3. Implement code to pass tests
4. Add frontend tests for toast integration

---

## Task Flow

```
Task 1 (Test) → Task 2 (Backend) → Task 4 (Frontend)
                                      ↘ Task 3 (Integration))
```

## Parallelization

| Group | Tasks | Reason |
|-------|-------|--------|
| A | 1, 2 | Test and backend can be done in parallel |

| Task | Depends On | Reason |
|------|------------|--------|
| 3 | 2 | Requires backend error handling |
| 4 | 3 | Requires error response structure |

---

## TODOs

- [ ] 1. Write failing tests for 502 error handling in trade_api.py

  **What to do**:
  - Add test for 502 status code response
  - Test retry logic with 502 (exponential backoff)
  - Test logging output for 502 vs 429

  **Must NOT do**:
  - Modify existing 429 tests

  **Parallelizable**: YES (with 2)

  **References**:
  - `backend/tests/test_trade_api.py:61-75` - Existing 429 test pattern (test_search_handles_429_retry)
  - `backend/trade_api.py:19-46` - Current _request() method

  **Acceptance Criteria**:
  - [ ] Test file created: `backend/tests/test_trade_api_502.py`
  - [ ] Test for 502 triggers retry: PASS
  - [ ] Test for 502 exponential backoff: PASS
  - [ ] Test for 502 error logging: PASS
  - [ ] pytest runs all tests → PASS (N tests, 0 failures)

- [ ] 2. Implement 502 retry logic in trade_api.py

  **What to do**:
  - Add 502 handling in `_request()` method
  - Add 502-specific logging (print statements)
  - Implement exponential backoff for 502 (longer than 429)
  - Update 429 handling to include logging

  **Must NOT do**:
  - Modify search() or fetch() methods
  - Change rate limit values

  **Parallelizable**: YES (with 1)

  **References**:
  - `backend/trade_api.py:19-46` - Current _request() method
  - `backend/tests/test_trade_api.py:61-75` - 429 test pattern

  **Acceptance Criteria**:
  - [ ] 502 status code triggers retry loop
  - [ ] 502 retry delay: starts at 5s, doubles each attempt
  - [ ] Console output shows "502 Bad Gateway" for 502 errors
  - [ ] Console output shows "429 Rate Limited" for 429 errors
  - [ ] pytest runs all tests → PASS

- [ ] 3. Install react-hot-toast and create ToastContainer

  **What to do**:
  - Run `npm install react-hot-toast`
  - Add Toaster component to App.tsx
  - Create toast hook/utility for reuse

  **Must NOT do**:
  - Add toast calls yet (Task 4)

  **References**:
  - `poe2-trends/src/App.tsx:1-20` - App entry point
  - `poe2-trends/package.json:12-18` - Current dependencies

  **Acceptance Criteria**:
  - [ ] Command: `cd poe2-trends && npm install react-hot-toast` → SUCCESS
  - [ ] `node_modules/react-hot-toast` directory exists
  - [ ] App.tsx imports Toaster component
  - [ ] Toaster renders in UI (visible on page)

- [ ] 4. Add toast notifications for errors in BatchAnalysis.tsx

  **What to do**:
  - Import `toast` from react-hot-toast
  - Add try/catch with toast.error() for API calls
  - Show specific messages for 429 vs 502

  **Must NOT do**:
  - Modify other pages (Sidebar, Settings, etc.)

  **References**:
  - `poe2-trends/src/pages/BatchAnalysis.tsx:49-94` - handleAnalyze function
  - `poe2-trends/src/components/Sidebar.tsx:97-101` - Existing alert patterns

  **Acceptance Criteria**:
  - [ ] 429 error shows toast: "Rate limited - slowing down..."
  - [ ] 502 error shows toast: "Server busy - retrying..."
  - [ ] Final failure shows toast: "Analysis failed: [error]"
  - [ ] BatchAnalysis.tsx uses react-hot-toast

- [ ] 5. Update error response structure in price_analyzer.py

  **What to do**:
  - Modify exception handling to include error type
  - Return structured error with type (429/502/other)
  - Update console logging

  **Must NOT do**:
  - Change analyze_gap() return value structure

  **References**:
  - `backend/price_analyzer.py:160-162` - Current exception handling
  - `backend/server.py:334-336` - Server error handling

  **Acceptance Criteria**:
  - [ ] Exceptions are logged with error type
  - [ ] Error messages include "429" or "502" in output
  - [ ] price_analyzer.py still returns expected structure

- [ ] 6. Run full test suite and verify

  **What to do**:
  - Run all pytest tests
  - Run frontend lint
  - Manual verification of toasts

  **References**:
  - `backend/tests/test_trade_api.py` - All existing tests
  - `poe2-trends/package.json:9` - lint script

  **Acceptance Criteria**:
  - [ ] Command: `pytest` → PASS
  - [ ] Command: `cd poe2-trends && npm run lint` → PASS
  - [ ] Manual: Start dev server, trigger error, verify toast appears

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 1 | `test(trade_api): add 502 error handling tests` | tests/test_trade_api_502.py | pytest |
| 2 | `feat(trade_api): handle 502 with retry and logging` | trade_api.py | pytest |
| 3 | `chore(frontend): add react-hot-toast` | package.json, App.tsx | npm install |
| 4 | `feat(frontend): add toast notifications for errors` | pages/BatchAnalysis.tsx | Manual verify |
| 5 | `refactor(analyzer): include error type in exceptions` | price_analyzer.py | pytest |
| 6 | `chore: run full test suite` | All modified files | pytest && npm run lint |

---

## Success Criteria

### Verification Commands
```bash
# Backend tests
pytest

# Frontend lint
cd poe2-trends && npm run lint

# Manual verification
cd poe2-trends && npm run dev
# Navigate to Batch Analysis
# Trigger API error
# Verify toast appears with correct message
```

### Final Checklist
- [ ] All "Must Have" present
- [ ] All "Must NOT Have" absent
- [ ] All tests pass
- [ ] Toast notifications work for 429 and 502
- [ ] Console clearly shows error type
