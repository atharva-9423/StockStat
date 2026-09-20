# 📊 StatStock

### Statistics & Probability Stock Analysis — from real market data

**StatStock** is a simple website that analyses any stock listed on **Investing.com** using real historical prices.
Type a company name, pick it, and the app calculates descriptive statistics, trend lines,
probability estimates and hypothesis tests — with charts, a NIFTY 50 comparison,
and downloadable **PDF / Excel / CSV** reports.

> 🎓 Built for academic learning. Not investment advice.

---

## ✨ What you can do

| Feature | What it means in plain words |
|---|---|
| 🔍 Live stock search | Start typing a company name — matches appear automatically |
| 📈 Full analysis | Mean, median, mode, standard deviation, min/max, CV and more |
| 📉 Trend line | Shows whether the price trended up or down (regression) |
| 🎲 Probability | How often the price rose one week later, historically |
| 🧪 Hypothesis test | A proper t-test you can re-run with your own values |
| ⚖️ NIFTY 50 comparison | Your stock vs the market index, side by side |
| 📄 Downloads | PDF report, Excel workbook (stock + NIFTY sheets), CSV file |
| ⌨️ Keyboard friendly | Arrow keys + Enter work in search results and tabs |

---

## 🧰 What you need (one-time)

1. **A computer** with Windows, Mac or Linux.
2. **Python 3.10 or newer** — check yours first:
   ```powershell
   python --version
   ```
   If Python is missing, install it from [python.org](https://www.python.org/downloads/)
   (on Windows, tick **“Add python.exe to PATH”** during installation).
3. **Internet connection** — prices are fetched live from Investing.com.

That is everything. No accounts, no keys, no payments.

---

## ⬇️ Download the source code

Get the full project as a ZIP file — one click, no GitHub account needed:

### 👉 [⬇️ Click here to download StockStat.zip](https://github.com/atharva-9423/StockStat/archive/refs/heads/master.zip)

Prefer to look at the code first? Browse it here: https://github.com/atharva-9423/StockStat

**After downloading, do this:**
1. Open your **Downloads** folder and find `StockStat-master.zip`.
2. **Right-click it → Extract All…** → choose a location (for example `Documents`) → click **Extract**.
3. Open the extracted `StockStat-master` folder — you will see `backend` and `frontend` folders inside.
4. Continue with **Step 1 of Setup below**, using *your* extracted location, for example:
   ```powershell
   cd "$HOME\Documents\StockStat-master\backend"
   ```

---

## 🚀 Setup — first time only (about 5 minutes)

Open **PowerShell** (press `Win + X` → *Terminal* / *Windows PowerShell*) and run
these commands **one by one**. Wait for each to finish before the next.

**Step 1 — go to the project folder** (the `backend` folder inside your extracted project)
```powershell
cd "$HOME\Documents\StockStat-master\backend"
```
> 💡 Replace the path above with wherever *you* extracted the project.

**Step 2 — create a private environment for the app**
```powershell
python -m venv .venv
```

**Step 3 — install everything the app needs**
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```
> ☕ This downloads several packages and can take a few minutes. That is normal.

**Step 4 — create your settings file**
```powershell
copy .env.example .env
```

✅ Setup is done. You never need to repeat these steps on this computer.

---

## ▶️ Running the app — every time

In PowerShell, from the `backend` folder:

```powershell
cd "$HOME\Documents\StockStat-master\backend"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Then open your browser and go to:

### 👉 http://127.0.0.1:8000

To stop the app later, press **Ctrl + C** in the PowerShell window.

> 🍎 **On Mac / Linux**, the commands are almost identical:
> `python3 -m venv .venv`, `source .venv/bin/activate`,
> `pip install -r requirements.txt`, `cp .env.example .env`,
> `python -m uvicorn app.main:app --reload --port 8000`.

---

## 🖱️ How to use the website

1. **Search** — type a company name (e.g. `ambuja`, `reliance`, `apple`, `tcs`).
   Results appear as you type. Press **↓** to move through them, **Enter** to select.
2. **Confirm** — the chosen stock appears in the search bar and its symbol is locked in below.
3. **Dates** — the period defaults to **01 Apr 2025 → 31 Mar 2026**.
   You can change both dates; the app checks they make sense.
4. **Analyze** — click **Analyze** and wait a few seconds (first run fetches fresh prices).
5. **Explore the tabs** — Overview · Statistics · NIFTY Comparison · Regression ·
   Probability · Hypothesis Test · Raw Data · Assignment. Use **← / →** to move between tabs.
6. **Download** — **PDF report**, **Excel** (separate sheets for stock + NIFTY raw data)
   or **CSV**, from the Overview tab or directly inside the Raw Data tab.

---

## 🗂️ Project map

```
StockStat/
├── backend/                 → the engine (Python)
│   ├── app/
│   │   ├── main.py          → starts the website + API
│   │   ├── config.py        → settings (reads the .env file)
│   │   ├── api/             → web addresses: search, analyze, downloads
│   │   ├── models/          → shapes of incoming requests
│   │   └── services/
│   │       ├── analysis.py        → fetches data, runs all the maths
│   │       ├── statistics.py / regression.py / probability.py / hypothesis.py
│   │       ├── data_cleaning.py   → checks and cleans price data
│   │       ├── report_generator.py→ builds the PDF
│   │       ├── cache.py           → remembers prices for 24 hours
│   │       └── market_data/       → Investing.com + Yahoo providers
│   ├── requirements.txt     → list of Python packages to install
│   ├── .env.example         → copy this to .env (your settings)
│   └── tests/               → automatic checks
└── frontend/                → the website you see
    ├── index.html           → page structure
    ├── css/app.css          → dark theme styling
    └── js/app.js            → search, charts, tabs, downloads
```

---

## ⚙️ Settings you can change (optional)

Open the `backend/.env` file in any text editor:

| Setting | Meaning | Default |
|---|---|---|
| `DATA_PROVIDER` | Where prices come from: `investing` or `yahoo` | `investing` |
| `DEFAULT_START` / `DEFAULT_END` | Default analysis dates | `2025-04-01` / `2026-03-31` |
| `CACHE_TTL_SECONDS` | How long prices are remembered (86400 = 24 h) | `86400` |

Restart the app after changing this file.

---

## 🧪 For developers — automatic checks

```powershell
cd "$HOME\Documents\StockStat-master\backend"
.\.venv\Scripts\python.exe -m pytest -q
```

Main API addresses (all start with `http://127.0.0.1:8000`):

| Address | What it does |
|---|---|
| `GET /api/health` | Is the server awake? |
| `GET /api/stocks/search?q=ambuja` | Find stocks |
| `POST /api/analyze` | Run a full analysis |
| `GET /api/report/{id}` | Download the PDF |
| `GET /api/export/{id}/excel` | Download the Excel workbook |
| `GET /api/export/{id}?kind=raw` | Download the CSV |

---

## 🆘 Troubleshooting — plain fixes

| Problem | Fix |
|---|---|
| `python` is not recognized | Reinstall Python with **“Add python.exe to PATH”** ticked |
| Port 8000 already in use | Close the other terminal, or use `--port 8001` and open `http://127.0.0.1:8001` |
| Excel button does nothing | Stop the server (Ctrl+C), start it again, hard-refresh the page (**Ctrl+F5**), click **Analyze** again, then download |
| “Market data could not be retrieved” | Check your internet and retry in a minute — Investing.com sometimes rate-limits |
| First analysis is slow | Normal — prices are being fetched; repeats are instant thanks to the cache |
| Downloads complain the analysis is gone | Restarting the server clears old results — just click **Analyze** again |

---

## ⚠️ Please note

- Prices come from **Investing.com (third-party)** — shown honestly as such in the app and reports.
- Figures are computed deterministically from fetched prices; statistics describe the past
  and do **not** predict the future.
- Academic project — **not investment advice**.

---

<div align="center">

**Made by Atharva Phatangare** ❤️

</div>
