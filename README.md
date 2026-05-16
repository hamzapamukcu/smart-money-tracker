# 📈 Smart Money Tracker

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/Streamlit-App-FF4B4B.svg" alt="Streamlit">
  <img src="https://img.shields.io/badge/Database-SQLite-003B57.svg" alt="SQLite">
  <img src="https://img.shields.io/badge/Docker-Supported-2496ED.svg" alt="Docker">
</div>

<p align="center">
  <b>An interactive dashboard to track investment patterns from US Congress members (STOCK Act) and institutional fund managers (SEC 13F filings).</b>
</p>

---

## 🌟 Features

- **🏛️ Senate Trades Feed**: Real-time STOCK Act trade feed with filters and late-disclosure flags.
- **🐋 Fund Tracker**: 13F holdings per fund, quarter-over-quarter diffs, treemaps, and historical position tracking.
- **🎯 Conviction Signals**: Cross-referenced conviction scores—discover which tickers the "smart money" is actively accumulating.
- **👀 My Watchlist**: Activity alerts and personalized insights for your favorite tickers.
- **🐳 Docker Support**: Easily run the application in an isolated environment without dependency issues.

## 🚀 Quick Start (Local Setup)

The easiest way to get started is by using the provided `Makefile` (if you are on Linux/macOS).

### 1. Clone the repository
```bash
git clone https://github.com/your-username/smart-money-tracker.git
cd smart-money-tracker
```

### 2. Configure Environment Variables
You need to set up a required `SEC_USER_AGENT` environment variable to fetch data from SEC EDGAR.
```bash
cp .env.example .env
```
Open `.env` in your text editor and provide your real name and email (required by the SEC):
```env
SEC_USER_AGENT=Jane Doe janedoe@example.com
```

### 3. Setup and Run via Makefile (Recommended)
We have prepared a `Makefile` to simplify the installation process.

```bash
# 1. Create a virtual environment and install dependencies
make setup

# 2. Initialize the database and fetch the latest SEC/Senate data
# Note: Expect 10-20 minutes for the initial data pull due to EDGAR rate limits.
make fetch-data

# 3. Start the interactive dashboard
make run
```
Once started, open your browser and navigate to **[http://localhost:8501](http://localhost:8501)**.

### Manual Setup (Without Makefile)
If you prefer not to use `make` or are on Windows:
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/init_db.py
streamlit run app/main.py
```

---

## 🐳 Running with Docker

Don't want to deal with Python environments? You can run everything via Docker!

### 1. Configure the `.env` file
```bash
cp .env.example .env
# Edit .env with your SEC_USER_AGENT
```

### 2. Run the application
```bash
make docker-run
# Or manually: docker-compose up --build
```

*Note: For the initial data pull, you must fetch the data while the container is running:*
```bash
make docker-fetch
# Or manually: docker-compose exec app python scripts/init_db.py
```

---

## 🏗️ Architecture & Project Structure

- **`app/`**: Streamlit dashboard (Main application, pages, and UI components)
- **`src/collectors/`**: Data ingestion modules (Senate API + SEC EDGAR fetchers)
- **`src/processors/`**: Logic engines (Diff engine for quarterly changes + signals scorer)
- **`src/database/`**: SQLAlchemy ORM models, connection configurations, and CRUD operations
- **`config/`**: System settings and predefined fund/congress watchlists
- **`scripts/`**: Utility scripts like `init_db.py` for one-time setup
- **`data/`**: Local SQLite database storage (`tracker.db`)

By default, the system uses **SQLite**. You can seamlessly switch to **PostgreSQL** by updating the `DATABASE_URL` in your `.env` file—zero code changes required!

## 📊 Tracked Entities

### 🏛️ Congress Members
All STOCK Act filers are captured. The UI flags notoriously high-activity members such as Tommy Tuberville, Mark Warner, Dan Sullivan, Sheldon Whitehouse, and Nancy Pelosi.

### 🐋 Institutional Funds
Tracks 18 top-tier institutional investors across value, macro, tech/growth, quant, and activist categories—including portfolios managed by Buffett, Burry, Druckenmiller, Soros, Wood, Griffin, and more. See `config/watchlists.py` for the complete list.

## 🤝 Contributing
Contributions are always welcome! Feel free to open an issue or submit a Pull Request to improve the tracker.

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).
