"""
Tracked funds and notable congress members.
Add/remove entries here — the rest of the app picks them up automatically.
"""

# SEC 13F filers: list of dicts with fund metadata + CIK
FUND_WATCHLIST: list[dict] = [
    # Classic / Value
    {"manager_name": "Warren Buffett",        "fund_name": "Berkshire Hathaway",       "cik": "0001067983", "category": "Classic/Value"},
    {"manager_name": "Bill Ackman",           "fund_name": "Pershing Square Capital",  "cik": "0001336528", "category": "Classic/Value"},
    {"manager_name": "Michael Burry",         "fund_name": "Scion Asset Management",   "cik": "0001649339", "category": "Classic/Value"},
    {"manager_name": "Seth Klarman",          "fund_name": "Baupost Group",            "cik": "0000901108", "category": "Classic/Value"},
    {"manager_name": "David Einhorn",         "fund_name": "Greenlight Capital",       "cik": "0001079114", "category": "Classic/Value"},
    {"manager_name": "Dan Loeb",              "fund_name": "Third Point",              "cik": "0001040792", "category": "Classic/Value"},
    {"manager_name": "Carl Icahn",            "fund_name": "Icahn Capital Management", "cik": "0000813672", "category": "Classic/Value"},
    # Macro
    {"manager_name": "Stanley Druckenmiller", "fund_name": "Duquesne Family Office",   "cik": "0001536411", "category": "Macro"},
    {"manager_name": "David Tepper",          "fund_name": "Appaloosa Management",     "cik": "0000931328", "category": "Macro"},
    {"manager_name": "Paul Tudor Jones",      "fund_name": "Tudor Investment Corp",    "cik": "0000886282", "category": "Macro"},
    {"manager_name": "George Soros",          "fund_name": "Soros Fund Management",   "cik": "0001029160", "category": "Macro"},
    # Tech / Growth
    {"manager_name": "Cathie Wood",           "fund_name": "ARK Investment Management","cik": "0001579982", "category": "Tech/Growth"},
    {"manager_name": "Chase Coleman",         "fund_name": "Tiger Global Management",  "cik": "0001167483", "category": "Tech/Growth"},
    {"manager_name": "Philippe Laffont",      "fund_name": "Coatue Management",        "cik": "0001336092", "category": "Tech/Growth"},
    # Multi-Strategy / Quant
    {"manager_name": "Ken Griffin",           "fund_name": "Citadel Advisors",         "cik": "0001423053", "category": "Multi-Strategy/Quant"},
    {"manager_name": "Israel Englander",      "fund_name": "Millennium Management",    "cik": "0001273931", "category": "Multi-Strategy/Quant"},
    {"manager_name": "Steve Cohen",           "fund_name": "Point72 Asset Management", "cik": "0001603291", "category": "Multi-Strategy/Quant"},
    # Activist
    {"manager_name": "Nelson Peltz",          "fund_name": "Trian Fund Management",   "cik": "0001418819", "category": "Activist"},
]

# CIK lookup helpers
FUND_BY_CIK: dict[str, dict] = {f["cik"]: f for f in FUND_WATCHLIST}
FUND_CIKS: list[str] = [f["cik"] for f in FUND_WATCHLIST]

# Congress members flagged for default prominence in the UI
HIGH_ACTIVITY_SENATORS: list[str] = [
    "Tommy Tuberville",
    "Mark Warner",
    "Dan Sullivan",
    "Sheldon Whitehouse",
    "Nancy Pelosi",
]

# Funds to watch for future 13F eligibility (< $100M AUM)
PENDING_WATCH_LIST: list[dict] = [
    {
        "manager_name": "Leopold Aschenbrenner",
        "fund_name": "Fortify",
        "note": "Founded 2024, AI/national-security focus. Check quarterly if >$100M AUM threshold crossed.",
    }
]
