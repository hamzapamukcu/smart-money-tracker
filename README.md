# Smart Money Tracker

Track investment patterns from US Congress members (STOCK Act) and institutional fund managers (SEC 13F filings) in an interactive Streamlit dashboard.

## Quick Start

### 1. Clone & set up

```bash
cd smart-money-tracker
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
```

Edit `.env` and set your `SEC_USER_AGENT` (required by SEC — use your real name and email):

```
SEC_USER_AGENT=Jane Doe janedoe@example.com
```

### 3. Initialise the database & fetch data

```bash
python scripts/init_db.py
```

This creates the SQLite database, fetches all Senate PTR filings, downloads 13F holdings for all 18 tracked funds, computes quarter-over-quarter diffs, and scores conviction signals. **Expect 10–20 minutes** the first time (EDGAR rate limits).

### 4. Run the dashboard

```bash
streamlit run app/main.py
```

Open [http://localhost:8501](http://localhost:8501).

---

## Pages

| Page | What you'll find |
|---|---|
| **Senate Trades** | Real-time STOCK Act trade feed with filters and late-disclosure flags |
| **Fund Tracker** | 13F holdings per fund, quarter-over-quarter diffs, treemap, position history |
| **Signals** | Cross-referenced conviction scores — tickers smart money is accumulating |
| **My Watchlist** | Activity alerts for your personal tickers |

---

## Docker (Phase 2)

```bash
docker-compose up --build
```

---

## Architecture

```
config/          — settings + fund/congress watchlists
src/collectors/  — Senate API + SEC EDGAR fetchers
src/processors/  — diff engine + signals scorer
src/database/    — SQLAlchemy models, connection, CRUD
app/             — Streamlit dashboard (main + 4 pages + components)
scripts/         — one-time init script
```

Database: SQLite locally (`data/tracker.db`). Switch to PostgreSQL by changing `DATABASE_URL` in `.env` — zero code changes required.

---

## Tracked Funds

18 institutional investors across value, macro, tech/growth, quant, and activist categories — including Buffett, Burry, Druckenmiller, Soros, Wood, Griffin, and more. See [`config/watchlists.py`](config/watchlists.py).

## Tracked Congress Members

All STOCK Act filers are stored. The following are flagged as high-activity in the UI: Tommy Tuberville, Mark Warner, Dan Sullivan, Sheldon Whitehouse, Nancy Pelosi.
