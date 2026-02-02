# Batch Analysis Improvements

## Context

### Original Request
1. Add clickable links to official PoE trade site when clicking on prices
2. Change base currency from Chaos Orbs to Exalted Orbs

### Current State
- Prices displayed in "c" (Chaos Orbs)
- No links on price columns
- Currency service normalizes to Chaos

---

## Work Objectives

### Core Objective
Add trade site links and change currency to Exalted

### Concrete Deliverables
- Clickable prices link to PoE trade search
- Display "Ex" instead of "c" for Exalted Orbs
- Currency calculations normalized to Exalted

### Definition of Done
- [ ] Prices are clickable links to PoE trade
- [ ] "Ex" displayed instead of "c"
- [ ] Currency calculations use Exalted as base

---

## Implementation Plan

### Task 1: Change Currency Base to Exalted

**What to do**:
- Update `currency_service.py` to normalize to Exalted
- Update exchange rates (1 Ex = X Chaos, 1 Ex = Y Divine)
- Update price_analyzer.py if needed

**Must NOT do**:
- Change currency rate values

### Task 2: Update Frontend Display

**What to do**:
- Change table headers from "(c)" to "(Ex)"
- Update price display to show "Ex" suffix
- Make price columns clickable links

**Links format**:
- Normal items: `https://www.pathofexile.com/trade2/search/poe2/Fate%20of%20the%20Vaal?type={base_type}&status=online`
- Magic items: Same with rarity filter

**Must NOT do**:
- Change other UI elements

---

## TODOs

- [ ] 1. Change currency base to Exalted in currency_service.py

  **What to do**:
  - Change `rates` to be normalized to Exalted (1 Ex = base)
  - 1 Ex = ~180 Chaos (or whatever current rate)
  - Update `normalize_to_exalted` method

  **References**:
  - `backend/currency_service.py:1-37` - Current currency service

  **Acceptance Criteria**:
  - [ ] normalize_to_exalted returns Exalted values
  - [ ] 1 Ex = 1.0, 180 Chaos = 1.0, etc.

- [ ] 2. Update price_analyzer.py to use Exalted

  **What to do**:
  - Change `normalize_to_chaos` to `normalize_to_exalted`
  - Update all references

  **References**:
  - `backend/price_analyzer.py` - Uses currency service

  **Acceptance Criteria**:
  - [ ] analyze_gap returns Exalted values

- [ ] 3. Update frontend table headers

  **What to do**:
  - Change "(c)" to "(Ex)" in table headers
  - Update column labels

  **References**:
  - `poe2-trends/src/pages/BatchAnalysis.tsx:210-213`

  **Acceptance Criteria**:
  - [ ] Headers show "Normal (Ex)", "Magic (Ex)"

- [ ] 4. Add clickable links to prices

  **What to do**:
  - Wrap price values in `<a>` tags
  - Link to PoE trade search URL
  - Open in new tab

  **URL format**:
  ```
  https://www.pathofexile.com/trade2/search/poe2/Fate%20of%20the%20Vaal?type={base_type}&status=online
  ```

  **References**:
  - `poe2-trends/src/pages/BatchAnalysis.tsx:228-231`

  **Acceptance Criteria**:
  - [ ] Clicking price opens trade search
  - [ ] Links open in new tab

- [ ] 5. Run tests and verify

  **What to do**:
  - Run pytest
  - Run frontend lint

  **Acceptance Criteria**:
  - [ ] All tests pass
  - [ ] Lint passes

---

## Commit Strategy

| After Task | Message | Files |
|------------|---------|-------|
| 1 | `refactor(currency): normalize to Exalted instead of Chaos` | currency_service.py |
| 2 | `refactor(analyzer): use Exalted normalization` | price_analyzer.py |
| 3 | `feat(frontend): update table headers to show Ex` | BatchAnalysis.tsx |
| 4 | `feat(frontend): add clickable trade links` | BatchAnalysis.tsx |
