# Plan: Enhance Backend Analysis & Frontend UX

## Context
1.  **Backend Logic**: The user wants to remove the 5-attempt limit for the price ramp. Instead, keep increasing price until T1 items are found (maybe cap at a very high limit like 100x or 20 attempts to avoid infinite loops, but "do not limit at 5" is the core request).
2.  **Frontend UX**: The user wants persistent memory (input/results), ability to cancel the search, and visible progress.

## Analysis Summary
- **Backend**: `PriceAnalyzer.analyze_gap` currently loops 5 times. We need to increase this limit or make it dynamic. Let's set it to 15-20 to cover a massive price range (2^20 is huge).
- **Frontend**: `BatchAnalysis.tsx` needs `localStorage` for state, `AbortController` for cancellation, and a progress bar.

## Work Objectives
- Update `PriceAnalyzer` to extend the search ramp.
- Update `BatchAnalysis.tsx` with Persistence, Cancellation, and Progress Bar.

## TODOs

- [x] 1. **Extend Backend Search Attempts**
    **What to do**:
    - Modify `backend/price_analyzer.py`.
    - Increase `range(5)` loop to `range(15)`.
    - This covers `start * 2^14` price multiplier. If `start` is 2c, max is 32,768c. That's effectively unlimited for PoE.
    
    **Verification**:
    - [x] `pytest backend/tests/test_price_analyzer.py` passes.

- [x] 2. **Implement Frontend Persistence**
    **What to do**:
    - Update `poe2-trends/src/utils/storage.ts`: Add `getBatchData` / `saveBatchData`.
    - Update `BatchAnalysis.tsx`: Load state on mount, save state on change/result.
    
    **Verification**:
    - [x] Code compiles.

- [x] 3. **Implement Frontend Cancellation & Progress**
    **What to do**:
    - Refactor `handleAnalyze` to use `AbortController`.
    - Add "Stop Analysis" button (replaces "Analyze" when loading).
    - Add Progress Bar (filled % based on `index / total`).
    - Add "Processing: [ItemName]" indicator.
    
    **Verification**:
    - [x] Manual or E2E check (optional). Lint check mandatory.

## 3. REQUIRED TOOLS
- Edit: To modify files.
- Bash: To run tests/lint.

## 4. MUST DO
- Backend: Increase loop count.
- Frontend: `AbortController`, `localStorage`.

## 5. MUST NOT DO
- Infinite loop without ANY cap.

## 6. CONTEXT
- User wants robust, cancellable, persistent long-running tasks.
