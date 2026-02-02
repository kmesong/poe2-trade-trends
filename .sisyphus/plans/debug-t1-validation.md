# Plan: Debug T1 Magic Item Validation

## Context
The user reports "no items have been found".
My analysis revealed two bugs in `backend/price_analyzer.py`:
1.  **Nesting Bug**: The validator accesses `item["extended"]`, but the correct path is `item["item"]["extended"]`.
2.  **Breadth Bug**: The validator iterates all mod groups (including implicit), failing on mods without tiers.

## Analysis Summary
- **Current Logic**: Fails because `extended` is nested inside `item`, and implicits (no tier) cause rejection.
- **Fix**: Update `_is_t1_magic` to access `item["item"]["extended"]` and only iterate `explicit`, `fractured`, `desecrated` groups.

## Work Objectives
- Fix `backend/price_analyzer.py`.
- Update `backend/tests/test_price_analyzer.py` to match real API structure.

## TODOs

- [x] 1. **Fix Validator Logic**
    **What to do**:
    - Modify `_is_t1_magic` in `backend/price_analyzer.py`.
    - Retrieve `item_data = item.get("item", {})`.
    - Retrieve `mods = item_data.get("extended", {}).get("mods", {})`.
    - Iterate only `group in ["explicit", "fractured", "desecrated"]`.
    
    **Verification**:
    - [x] `pytest backend/tests/test_price_analyzer.py` (after Step 2).

- [x] 2. **Update Tests**
    **What to do**:
    - Modify `backend/tests/test_price_analyzer.py`.
    - Update mocks to wrap `extended` inside `item`.
    - Add a test case with implicit mods (no tier) to ensure they are ignored.
    
    **Verification**:
    - [x] `pytest backend/tests/test_price_analyzer.py` passes.

## 3. REQUIRED TOOLS
- Edit: To modify files.
- Bash: To run tests.

## 4. MUST DO
- Handle nesting.
- Ignore implicits.

## 5. MUST NOT DO
- Break existing logic for `listing`.

## 6. CONTEXT
- "show me how you determine an item has all t1 modifiers" -> fixing this logic answers that.
