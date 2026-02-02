# Batch Analysis - Item Tree Selector

## Context

### Original Request
Replace manual text input for batch analysis with a tree view with checkboxes populated from PoE items API.

### API Endpoint
```
GET https://www.pathofexile.com/api/trade2/data/items
```

### Expected Data Structure
The API returns a JSON structure with item categories and items. Users will select items via checkboxes in a tree hierarchy.

---

## Work Objectives

### Core Objective
Replace textarea input with checkbox tree selector

### Concrete Deliverables
- Backend endpoint to proxy items API (to avoid CORS issues)
- Frontend item tree component with checkboxes
- Selected items state management
- Integration with existing batch analysis

### Definition of Done
- [ ] Backend proxy endpoint for items API
- [ ] Tree component with categories and items
- [ ] Checkbox selection with parent/child propagation
- [ ] Selected items passed to batch analysis
- [ ] UI shows count of selected items

### Must Have
- Categories (Body Armors, Helmets, etc.)
- Individual item checkboxes
- Select all / Deselect all buttons
- Search/filter capability

### Must NOT Do
- Modify existing batch analysis logic (only the input method)

---

## Implementation Plan

### Task 1: Add Backend Proxy Endpoint

**What to do**:
- Add `GET /api/items` endpoint in `server.py`
- Proxy request to `https://www.pathofexile.com/api/trade2/data/items`
- Add proper headers (User-Agent, etc.)
- Handle errors gracefully

**References**:
- `backend/server.py` - Existing API endpoints

**Acceptance Criteria**:
- [ ] GET `/api/items` returns item data
- [ ] CORS handled correctly
- [ ] Error handling returns empty array on failure

### Task 2: Create Item Tree Component

**What to do**:
- Create `src/components/ItemTree.tsx`
- Fetch items from `/api/items`
- Display categories as collapsible sections
- Display items as checkboxes within categories
- Handle checkbox clicks with proper propagation

**State Structure**:
```typescript
interface ItemData {
  id: string;
  name: string;
  category: string;
}

interface ItemTreeProps {
  onSelectionChange: (selected: string[]) => void;
}
```

**Acceptance Criteria**:
- [ ] Categories collapsible
- [ ] Checkboxes for each item
- [ ] Parent checkbox toggles all children
- [ ] Individual selection works

### Task 3: Add Search/Filter to Tree

**What to do**:
- Add search input above tree
- Filter items by name in real-time
- Show filtered results with category context

**Acceptance Criteria**:
- [ ] Search filters items
- [ ] Results show category context
- [ ] Clear search button

### Task 4: Update BatchAnalysis Page

**What to do**:
- Replace textarea with ItemTree component
- Update state to use array of selected items
- Add "Selected: X items" display
- Add "Analyze Selected" button

**References**:
- `poe2-trends/src/pages/BatchAnalysis.tsx` - Current implementation

**Acceptance Criteria**:
- [ ] Textarea removed
- [ ] ItemTree displayed
- [ ] Selection passed to analyze function
- [ ] Count shown (e.g., "15 items selected")

### Task 5: Run Tests and Verify

**What to do**:
- Run pytest
- Run frontend lint
- Manual verification

**Acceptance Criteria**:
- [ ] All tests pass
- [ ] Lint passes
- [ ] Manual: Tree displays correctly
- [ ] Manual: Selection works

---

## Commit Strategy

| After Task | Message | Files |
|------------|---------|-------|
| 1 | `feat(api): add items proxy endpoint` | server.py |
| 2 | `feat(ui): create item tree component` | src/components/ItemTree.tsx |
| 3 | `feat(ui): add search filter to tree` | ItemTree.tsx |
| 4 | `feat(batch): replace textarea with tree` | BatchAnalysis.tsx |
| 5 | `chore: run full test suite` | All modified files |

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
# Navigate to Batch Analysis
# Verify tree displays with categories
# Select items
# Click analyze
# Verify analysis runs
```

### Final Checklist
- [ ] Tree displays categories/items
- [ ] Checkboxes work correctly
- [ ] Search filters items
- [ ] Analysis runs on selected items
- [ ] All tests pass
