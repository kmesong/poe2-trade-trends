# Plan: Create AGENTS.md

## Context
The user requested the creation of an `AGENTS.md` file to serve as a guide for AI agents. This file should contain build/test commands, code style guidelines, and agent behaviors.

## Analysis Summary
- **Backend**: Python/Flask. Uses `pytest`. Code style is `snake_case`, minimal docstrings, absolute imports.
- **Frontend**: React/Vite/TypeScript. Uses `npm run lint`, `React.FC`. Tailwind CSS.
- **Structure**: Monorepo with `backend/` and `poe2-trends/`.

## Work Objectives
- Create `AGENTS.md` in the project root with comprehensive guidelines (~150 lines).

## TODOs

- [ ] 1. **Create AGENTS.md**
    **What to do**:
    - Write the `AGENTS.md` file to the project root.
    - Content must include Project Overview, Environment Setup, Code Style (Python/React), Testing, and Agent Behavior.
    
    **Content to Write**:
    ```markdown
    # AGENTS.md

    This document provides context, commands, and guidelines for AI agents working in this repository.
    It is the single source of truth for coding standards, workflows, and environment setup.

    ## 1. Project Overview

    This is a monorepo containing a Path of Exile 2 trade analysis tool.

    - **Backend (`backend/`)**: 
      - Python Flask server.
      - Handles API requests to `pathofexile.com/api/trade2`.
      - Performs data processing, caching (`saved_data/`), and rate limiting.
      - Exposes endpoints for the frontend (e.g., `/analyze/batch-price`).

    - **Frontend (`poe2-trends/`)**: 
      - React 19 + TypeScript + Vite application.
      - Provides the UI for analysis, visualization, and settings.
      - Uses Tailwind CSS for styling.

    ## 2. Environment Setup & Commands

    ### Backend (Python)
    The root directory for backend context is `backend/`. 
    **CRITICAL**: Always activate the virtual environment or ensure dependencies are installed before running.

    *   **Install Dependencies**:
        ```bash
        pip install -r backend/requirements.txt
        pip install -r backend/requirements-dev.txt
        ```

    *   **Run Server**:
        The server runs on `http://localhost:5000`.
        ```bash
        # From project root
        python run_server.py
        # OR
        python -m backend.server
        ```

    *   **Run Tests**:
        Uses `pytest`. Tests are located in `backend/tests/`.
        ```bash
        # Run all tests
        pytest
        
        # Run a specific test file
        pytest backend/tests/test_trade_api.py
        
        # Run a specific test function (useful for TDD)
        pytest backend/tests/test_price_analyzer.py::test_analyze_gap_success -v
        ```

    ### Frontend (React/TS)
    The root directory is `poe2-trends/`.

    *   **Install Dependencies**:
        ```bash
        cd poe2-trends
        npm install
        ```

    *   **Start Dev Server**:
        The app runs on `http://localhost:5173`.
        ```bash
        cd poe2-trends
        npm run dev
        ```

    *   **Lint**:
        Always run lint before committing changes to frontend code.
        ```bash
        cd poe2-trends
        npm run lint
        ```

    *   **Build**:
        ```bash
        cd poe2-trends
        npm run build
        ```

    ## 3. Code Style Guidelines

    ### Backend (Python)
    *   **Naming**: 
        - Functions/Variables: `snake_case` (e.g., `get_session_id`, `analyze_gap`).
        - Classes: `PascalCase` (e.g., `TradeAPI`, `PriceAnalyzer`).
        - Constants: `UPPER_SNAKE_CASE` (e.g., `SEARCH_URL_BASE`).
    *   **Type Hints**: Encouraged but not strictly enforced. Use standard `typing` module.
    *   **Docstrings**: 
        - Minimalist triple-quote style. 
        - Short, descriptive summary immediately after definition.
        - Example: `"""Extract session ID from header or environment."""`
    *   **Imports**: 
        - Standard Library -> Third Party (Flask, Requests) -> Local Application.
        - Use absolute imports (e.g., `from backend.trade_api import TradeAPI`).
    *   **Error Handling**: 
        - Wrap API routes in `try...except Exception`.
        - Return JSON errors with 4xx/5xx codes: `return jsonify({"error": str(e)}), 500`.
        - Use `response.raise_for_status()` for external API calls.

    ### Frontend (React/TypeScript)
    *   **Components**: 
        - Use **Functional Components** with `React.FC`.
        - Named exports preferred.
        - Example: `export const BatchAnalysis: React.FC = () => { ... }`.
    *   **Props**: 
        - Define interfaces locally as `interface Props` or specific names (e.g., `BatchResult`).
        - Import shared types from `../types`.
    *   **Hooks**: 
        - Use `useState`, `useEffect`. 
        - Avoid complex logic in `useEffect`; extract to handlers.
    *   **Styling**: 
        - **Tailwind CSS** exclusively. Avoid CSS modules or inline styles.
        - Use custom colors from `tailwind.config.js` (e.g., `bg-poe-bg`, `text-poe-gold`).
    *   **File Naming**: 
        - Components/Pages: `PascalCase.tsx` (e.g., `Sidebar.tsx`).
        - Utilities: `camelCase.ts` (e.g., `storage.ts`).

    ## 4. Directory Structure Conventions

    ### Backend
    - `backend/server.py`: Main Flask entry point.
    - `backend/tests/`: Pytest tests.
    - `backend/*.py`: Services and logic modules (e.g., `price_analyzer.py`).

    ### Frontend
    - `src/components/`: Reusable UI elements (Sidebar, Grid).
    - `src/pages/`: Full-page views mapped to Routes (BatchAnalysis, Settings).
    - `src/utils/`: Helper functions (storage, formatters).
    - `src/types.ts`: Centralized TypeScript definitions.

    ## 5. Agent Behavior & Workflows

    *   **Atomic Changes**: Focus on one task at a time. Verify functionality before moving to the next.
    *   **No "Blind" Fixes**: If a test fails, read the error output carefully. Do not guess.
    *   **File Edits**: Use `Edit` tool for precise changes. Avoid rewriting entire files unless necessary.
    *   **Testing**:
        - **Backend**: Always run `pytest` after modifying Python code.
        - **Frontend**: Run `npm run lint` to catch syntax/type errors.
        - **E2E**: Use `playwright` or manual verification for UI flows.

    ## 6. Tech Stack Details

    - **Backend**: Python 3.11+, Flask, Requests, Pytest.
    - **Frontend**: React 19, TypeScript 5, Vite, Tailwind CSS.
    - **External APIs**: Path of Exile 2 Trade API (requires Session ID).
    - **Data Persistence**: Local JSON files (`saved_data/`) and browser `localStorage`.
    ```

    **Verification**:
    - [ ] File `AGENTS.md` exists.
    - [ ] Content matches the requirements.
