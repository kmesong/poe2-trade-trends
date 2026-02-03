# AGENTS.md

This document provides context, commands, and guidelines for AI agents working in this repository.

## 1. Project Overview

This is a monorepo containing a Path of Exile 2 trade analysis tool.
- **Backend**: Python Flask server (`backend/`). Handles API requests, data fetching, and processing.
- **Frontend**: React/TypeScript Vite application (`poe2-trends/`). Provides the UI for analysis and visualization.

## 2. Build, Lint, and Test Commands

### Backend (Python)

*   **Install Dependencies**:
    ```bash
    pip install -r backend/requirements.txt
    pip install -r backend/requirements-dev.txt
    ```

*   **Run Server**:
    ```bash
    python run_server.py
    # OR
    python -m backend.server
    ```
    Server runs on `http://localhost:5000`.

*   **Run Tests**:
    ```bash
    pytest                          # Run all tests
    pytest backend/tests/           # Run all tests in directory
    pytest backend/tests/test_trade_api.py  # Run specific test file
    pytest -v backend/tests/test_trade_api.py::test_search_handles_429_retry  # Run single test
    pytest -k "trade_api"          # Run tests matching pattern
    ```

### Frontend (React/TS)

Root directory is `poe2-trends/`.

*   **Install Dependencies**:
    ```bash
    cd poe2-trends && npm install
    ```

*   **Start Dev Server**:
    ```bash
    cd poe2-trends && npm run dev
    ```
    App runs on `http://localhost:5173`.

*   **Lint**:
    ```bash
    cd poe2-trends && npm run lint
    ```

*   **Build**:
    ```bash
    cd poe2-trends && npm run build
    ```

## 3. Code Style Guidelines

### Backend (Python)

| Category | Convention |
|----------|------------|
| **Naming** | `snake_case` for functions/variables, `PascalCase` for classes |
| **Type Hints** | Optional but encouraged for complex logic |
| **Imports** | Standard Library → Third Party (Flask, Requests) → Local Application |
| **Error Handling** | Use `try...except` for external API calls. Return `jsonify({"error": "..."}), 400` in Flask |
| **API Clients** | Use dedicated classes (e.g., `TradeAPI`). Use `requests.Session` with proper headers/timeouts |
| **Constants** | UPPER_SNAKE_CASE for configuration values |

### Frontend (React/TypeScript)

| Category | Convention |
|----------|------------|
| **Naming** | `PascalCase` for components/files, `camelCase` for variables/functions |
| **Type Imports** | Use `import type { ... }` for type-only imports (required by `verbatimModuleSyntax: true`) |
| **Components** | Top-level: `function App() {}`, Smaller: `const Component: React.FC = () => {}` |
| **Styling** | Tailwind CSS exclusively. Use `poe-*` colors (`bg-poe-bg`, `text-poe-gold`) |
| **State** | React Hooks (`useState`, `useEffect`). Avoid class components |
| **Types** | Centralize shared interfaces in `src/types.ts` |
| **Directories** | `src/components/` (UI), `src/pages/` (routes), `src/utils/` (helpers), `src/services/` (API) |

**TypeScript Strict Mode Rules** (tsconfig.app.json):
- `verbatimModuleSyntax: true` → Must use `import type` for types
- `noUnusedLocals: true` → No unused variables
- `noUnusedParameters: true` → No unused function parameters

### Tailwind CSS Colors

Available `poe-*` colors:
- `poe-bg` (#0a0a0a), `poe-card` (#141414), `poe-border` (#2a2a2a)
- `poe-gold` (#c8aa6d), `poe-golddim` (#8a754c)
- `poe-text` (#a38d6d), `poe-highlight` (#fff4d6), `poe-red` (#bd3333)

## 4. Testing Guidelines

### Backend
- Use `pytest` for all backend testing
- **MUST** mock external network calls using `requests-mock`. Never hit real POE Trade API
- Tests located in `backend/tests/`
- Mock currency service with `MagicMock` in tests

### Frontend
- Verify UI changes via running dev server
- Run `npm run lint` before committing
- Use react-hot-toast for user feedback

## 5. Import Patterns

### Python (backend/)
```python
# Standard Library
import json
import time
from collections import defaultdict

# Third Party
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

# Local Application
from backend.price_analyzer import PriceAnalyzer
from backend.currency_service import CurrencyService
```

### TypeScript (poe2-trends/src/)
```typescript
// React/Node built-ins
import React, { useState, useEffect } from 'react';

// External libraries
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';

// Types (MUST use 'type' keyword - required by verbatimModuleSyntax)
import type { BatchResult, WeaponData } from '../types';

// Local utilities
import { getSessionId, saveSessionId } from '../utils/storage';
```

## 6. Error Handling Patterns

### Python Flask
```python
try:
    # External API call
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return jsonify(response.json())
except requests.exceptions.HTTPError as e:
    return jsonify({"error": f"API request failed: {str(e)}"}), 502
except Exception as e:
    return jsonify({"error": str(e)}), 500
```

### React TypeScript
```typescript
try {
    const response = await fetch('/api/endpoint');
    if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Request failed');
    }
    return await response.json();
} catch (err) {
    if (err instanceof Error) {
        setError(err.message);
        toast.error(err.message);
    }
    return null;
}
```

## 7. Agent Behavior

- **Atomic Changes**: Focus on one task at a time. Verify before moving to the next.
- **No "Blind" Fixes**: If a test fails, read the error output carefully. Do not guess.
- **File Edits**: Use `Edit` tool for precise changes. Avoid rewriting entire files.
- **Type Safety**: Never use `as any`, `@ts-ignore`, or suppress type errors.
- **Error Handling**: Never leave empty `catch(e) {}` blocks.

## 8. Common Issues & Fixes

### TypeScript Import Error: "doesn't provide an export named 'X'"

**Error**:
```
Uncaught SyntaxError: The requested module 'http://localhost:5173/src/types.ts' 
doesn't provide an export named: 'BatchResult'

# Or for other types:
Uncaught SyntaxError: The requested module 'http://localhost:5173/src/services/currencyRates.ts' 
doesn't provide an export named: 'CurrencyRates'
```

**Cause**: The codebase uses `verbatimModuleSyntax: true` in tsconfig.app.json, which requires type-only imports to use the `type` keyword.

**Fix**: Change regular imports to type-only imports:
```typescript
// WRONG - from types.ts
import { BatchResult } from '../types';

// CORRECT - from types.ts
import type { BatchResult } from '../types';

// WRONG - from any file exporting types
import { CurrencyRates } from '../services/currencyRates';

// CORRECT - from any file exporting types
import type { CurrencyRates } from '../services/currencyRates';
```

**Files affected**: Any file importing types from `src/types.ts`, `src/services/`, or other type definitions. Check with:
```bash
grep -r "import {.*} from" poe2-trends/src --include="*.tsx"
grep -r "import {.*} from" poe2-trends/src --include="*.ts"
```

**Fix all type imports from types.ts**:
```bash
cd poe2-trends
sed -i "s/import { \([A-Za-z]*\) } from '\.\.\/types';/import type { \1 } from '\.\.\/types';/g" src/**/*.tsx
```

**Pattern to fix types from services**:
```bash
# Check for types imported from services
grep -r "import {.*CurrencyRates.*} from" src/

# Then fix manually:
sed -i "s/import { \(.*\), CurrencyRates } from '\.\.\/services\/currencyRates';/import { \1, type CurrencyRates } from '\.\.\/services\/currencyRates';/g" src/**/*.tsx
```

## 9. Lessons Learned & Architecture Decisions

### Database Strategy (MongoDB vs SQL)
- **Decision**: Use MongoDB (`mongoengine`) instead of SQL (`SQLAlchemy`).
- **Reason**: 
  - Trade data is naturally hierarchical (Items -> Modifiers).
  - SQL drivers in Python (especially for Turso/LibSQL) faced severe compatibility issues (`ValueError: Hrana: api error: status=308`, missing PyPI packages for Python < 3.12).
  - MongoDB drivers (`pymongo`) are stable and widely supported.
- **Lesson**: Avoid `flask-mongoengine` (deprecated/unmaintained). Use pure `mongoengine` with manual connection handling.

### Async Processing & Timeouts
- **Problem**: Batch analysis iterates through items with a 2-second rate limit delay. For 30 items, this takes 60s+, triggering Gunicorn's default 30s timeout (`WORKER TIMEOUT`).
- **Solution**: 
  1. **Job Queue**: Implemented a MongoDB-backed Job system (`Job` model).
  2. **Background Workers**: Use `ThreadPoolExecutor` in Flask to process tasks off the main thread.
  3. **Frontend Polling**: The UI submits a job and polls `/api/jobs/<id>` instead of waiting for a long HTTP response.
- **Guideline**: NEVER perform loop-based or external API dependent tasks directly in a Flask request handler if they can exceed 30 seconds. Always offload to a background thread/worker.

### Python Versions
- **Constraint**: Modern drivers (like `libsql-experimental`) often require Python 3.10+.
- **Action**: Dockerfile upgraded to `python:3.12-slim`. Always check driver compatibility before downgrading Python.

### Protocol Handling (Legacy)
- *Historical context for SQL*: If forced to use Turso/LibSQL, use `sqlite+wss://` scheme and strip trailing slashes from the URL to avoid 308 Redirect loops.

