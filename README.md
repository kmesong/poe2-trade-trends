# PoE2 Trade Trends Dashboard

A powerful analytics dashboard for Path of Exile 2 that fetches live trade data to identify "Best in Slot" meta trends, popular affixes, and item valuations.

![Dashboard Preview](https://via.placeholder.com/800x400?text=PoE2+Trade+Trends+Dashboard)

## 🚀 Features

*   **Live Data Analysis**: Connects directly to the official PoE2 Trade API to fetch real-time market data.
*   **Affix Breakdown**: Automatically classifies modifiers into **Prefix**, **Suffix**, **Implicit**, **Rune** (Enchant), and **Bonded** types.
*   **Visual Dashboard**: Interactive UI to browse stats by item type (Bows, Wands, etc.).
*   **Custom Queries**: Paste your own PoE Trade JSON queries to analyze specific market segments (e.g., "Mirrored Bows with Physical Damage").
*   **Meta Discovery**: See which mods are appearing on 100% of top-tier items to guide your crafting or purchasing decisions.

## 🛠️ Prerequisites

*   **Python 3.8+** (for the backend data fetcher)
*   **Node.js 16+** (for the frontend dashboard)

## 📦 Installation

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd poe2-trends-project
```

### 2. Backend Setup (Python)
Navigate to the root directory and install the required Python packages:

```bash
pip install flask flask-cors requests
```

### 3. Frontend Setup (React/Vite)
Navigate to the frontend directory and install dependencies:

```bash
cd poe2-trends
npm install
```

## 🏃‍♂️ Usage

To use the tool, you need to run both the backend server (to handle API requests) and the frontend client (to display the dashboard).

### Step 1: Start the Backend Server
Open a terminal in the **project root** directory:

```bash
python backend/server.py
```
*   *This will start a local server on `http://localhost:5000`.*

### Step 2: Start the Dashboard
Open a new terminal in the **`poe2-trends`** directory:

```bash
npm run dev
```
*   *This will start the UI on `http://localhost:5173` (usually).*

### Step 3: Analyze Data
1.  Open the dashboard in your browser.
2.  Go to the official [Path of Exile 2 Trade Website](https://www.pathofexile.com/trade2/search/poe2).
3.  Perform a search (e.g., filter for "Mirrored" items, specific weapon types, etc.).
4.  Click the **"Copy Query"** button on the trade site to get the JSON payload.
5.  Paste the JSON into the **"Paste Trade Query JSON"** box in the dashboard sidebar.
6.  Click **"ANALYZE TRADE DATA"**.

The dashboard will fetch the latest 100 items for that query, analyze their modifiers, and update the view instantly.

## 📂 Project Structure

*   **`backend/`**
    *   `server.py`: Flask API server that proxies requests to PoE Trade and performs statistical analysis.
*   **`poe2-trends/`**
    *   `src/`: React frontend source code.
    *   `public/stats.json`: Default dataset loaded on startup.
*   **`analyze_api_stats.py`**: Standalone script to run analysis from the command line without the server.

## ⚠️ Note on Rate Limiting
This tool respects Path of Exile's API rate limits. Fetches are batched and delayed slightly to prevent IP bans. Analyzing large datasets may take a few seconds.

## 🤝 Contributing
Feel free to open issues or submit pull requests if you have ideas for better statistical analysis or new dashboard features!
