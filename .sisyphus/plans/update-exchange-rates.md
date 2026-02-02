# Update Exchange Rates from poe.ninja

## Context

### Original Request
Update currency exchange rates to use actual current rates from poe.ninja with a refresh button.

### Current State
- `currency_service.py` uses hardcoded approximate rates (1 Ex = 180 Chaos)
- poe.ninja loads rates dynamically (need to scrape or use API)
- No rate refresh functionality exists

### Plan Summary
1. Hardcode current approximate rates from poe.ninja
2. Add backend endpoint to fetch/scrape rates from poe.ninja
3. Add "Refresh Rates" button in Settings page

---

## Work Objectives

### Core Objective
Live currency rates from poe.ninja with manual refresh capability

### Concrete Deliverables
- Updated `currency_service.py` with accurate hardcoded rates
- Backend endpoint `/api/currency/rates` to fetch from poe.ninja
- "Refresh Rates" button in Settings page
- Rates persisted to localStorage or backend

### Definition of Done
- [ ] Hardcoded rates match poe.ninja (approximate)
- [ ] Settings page has "Refresh Rates" button
- [ ] Clicking button fetches new rates from poe.ninja
- [ ] Rates are displayed and used in calculations

### Must Have
- Hardcoded current rates
- Refresh button functionality
- Rates persist between sessions

### Must NOT Have
- Complex scraping logic (keep simple)
- Authentication for poe.ninja (use public data)

---

## Implementation Plan

### Task 1: Hardcode Current Rates

**What to do**:
- Update `currency_service.py` with current approximate rates from poe.ninja
- Common rates (verify on poe.ninja):
  - Chaos Orb ≈ 1/180 Exalted
  - Divine Orb ≈ 0.5 Exalted (90/180)
  - Alchemy Orb ≈ 0.0028 Exalted (0.5/180)
  - GCP ≈ 0.011 Exalted (2/180)
  - Regal Orb ≈ 0.0056 Exalted (1/180)
  - Vaal Orb ≈ 0.0083 Exalted (1.5/180)

**References**:
- `backend/currency_service.py` - Current rates

**Acceptance Criteria**:
- [ ] Rates normalized to Exalted (1 Ex = 1.0)
- [ ] Comments note rates are approximate and can be refreshed

### Task 2: Add Rate Fetch Endpoint

**What to do**:
- Add `/api/currency/rates` GET endpoint in `server.py`
- Fetch from poe.ninja page
- Parse currency values (simplified scraping)
- Return rates in same format as currency_service

**What to do if scraping fails**:
- Return hardcoded fallback rates
- Log warning

**References**:
- `backend/server.py` - Flask routes
- `backend/currency_service.py` - Rate format

**Acceptance Criteria**:
- [ ] GET `/api/currency/rates` returns JSON rates
- [ ] Response includes all currency types
- [ ] Falls back to hardcoded if fetch fails

### Task 3: Add Frontend Rate Service

**What to do**:
- Create `src/services/currencyRates.ts`
- Fetch rates from backend
- Persist to localStorage
- Provide `getRates()`, `refreshRates()` functions

**References**:
- `poe2-trends/src/utils/storage.ts` - Storage pattern

**Acceptance Criteria**:
- [ ] Service can fetch from backend
- [ ] Rates cached in localStorage
- [ ] `refreshRates()` triggers API call

### Task 4: Add Refresh Button to Settings

**What to do**:
- Add "Currency Rates" section to Settings page
- Display current rates
- Add "Refresh from poe.ninja" button
- Show loading state and success/error feedback

**References**:
- `poe2-trends/src/pages/Settings.tsx` - Settings page

**Acceptance Criteria**:
- [ ] Current rates displayed
- [ ] "Refresh Rates" button works
- [ ] Toast notification on success/error

### Task 5: Integrate with Batch Analysis

**What to do**:
- Update BatchAnalysis to use currencyRates service
- Display current rates (optional)
- Ensure prices update after refresh

**References**:
- `poe2-trends/src/pages/BatchAnalysis.tsx` - Uses currency

**Acceptance Criteria**:
- [ ] Prices recalculated after rate refresh

### Task 6: Run Tests and Verify

**What to do**:
- Run pytest
- Run frontend lint
- Manual verification

**Acceptance Criteria**:
- [ ] All tests pass
- [ ] Lint passes
- [ ] Manual: Refresh button works

---

## Commit Strategy

| After Task | Message | Files |
|------------|---------|-------|
| 1 | `refactor(currency): update hardcoded rates from poe.ninja` | currency_service.py |
| 2 | `feat(api): add currency rates fetch endpoint` | server.py |
| 3 | `feat(frontend): add currency rate service` | src/services/currencyRates.ts |
| 4 | `feat(ui): add refresh rates button to settings` | Settings.tsx |
| 5 | `feat(integration): use rate service in batch analysis` | BatchAnalysis.tsx |
| 6 | `chore: run full test suite` | All modified files |

---

## Success Criteria

### Verification Commands
```bash
# Backend tests
pytest  # → PASS

# Frontend lint
cd poe2-trends && npm run lint  # → PASS

# Manual verification
cd poe2-trends && npm run dev
# Navigate to Settings
# Click "Refresh Rates"
# Verify toast appears
```

### Final Checklist
- [ ] Hardcoded rates accurate
- [ ] Refresh button in Settings
- [ ] Rates fetch from poe.ninja
- [ ] All tests pass
