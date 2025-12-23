# Budgeting_Calculator
This app will help you budget based on your bank statements

## PROJECT OVERVIEW

This project is a personal finance analysis and budgeting system built in Python. It ingests credit card transaction data (currently designed for Chase CSV exports), normalizes and categorizes spending, stores everything in a local SQLite database, and provides analytics, visualizations, and AI-generated insights about spending habits.

The goal is to move beyond simple spreadsheets and create a durable, extensible system that can answer questions like:

* Where did my money go this year?
* Which categories and merchants drive most of my spending?
* How does my spending change month to month?
* What budgeting strategies would actually help based on my real data?

The system is designed so that all calculations are deterministic and auditable, and the AI layer is used only to interpret and explain results that are already computed.

---

## HIGH-LEVEL ARCHITECTURE

The project is split into three logical layers:

1. Ingestion and normalization
   Raw CSV files are parsed, cleaned, normalized, deduplicated, and written into a SQLite database. Category override rules are applied here.

2. Analytics and visualization
   Queries run against SQLite to produce monthly and yearly summaries, category breakdowns, and interactive Plotly charts.

3. AI insight generation
   A lightweight agent reads precomputed metrics and produces a narrative year-end report with conclusions and budgeting strategies.

The SQLite database is the single source of truth. CSV files are considered disposable after ingestion.

---

## DIRECTORY STRUCTURE (TYPICAL)

Budgeting Calculator/
venv/                         Python virtual environment
data/                         Raw CSV files (Chase exports)
budget.db                     SQLite database (created automatically)

ingest_chase_to_sqlite.py     CSV ingestion + normalization
analytics_sqlite.py           Queries SQLite and generates charts
agent_yearly_report.py        AI agent for yearly spending analysis
main.py                       Plotting functions (current location)
README.txt                    This file

You may later refactor plotting functions into a separate file (for example, plots.py), but this is optional.

---

## VIRTUAL ENVIRONMENT SETUP

This project assumes you are using a Python virtual environment.

Typical setup:

1. Create a virtual environment using Python 3.13:
   python -m venv venv

2. Activate it:
   source venv/bin/activate

3. Install dependencies:
   python -m pip install pandas plotly matplotlib openai

Always run scripts using the virtual environment’s Python interpreter:
./venv/bin/python script_name.py

This avoids conflicts with system or Homebrew Python installations.

---

## INGESTING TRANSACTION DATA

The ingestion script reads Chase credit card CSV exports and writes normalized data into SQLite.

Command example:
./venv/bin/python ingest_chase_to_sqlite.py 
--csv data/chase_statement.csv 
--account "Chase Sapphire Reserve"

What ingestion does:

* Parses transaction and post dates
* Normalizes merchant names
* Applies category override rules
* Converts money to integer cents for precision
* Deduplicates transactions using a hash
* Inserts rows into the SQLite database

You can ingest multiple CSVs over time. Duplicate transactions are automatically skipped.

---

## CATEGORY OVERRIDE RULES

Chase’s default categories are often noisy. This project supports explicit override rules stored in the database.

Rule types:

* EXACT: exact merchant match
* CONTAINS: substring match
* REGEX: regular expression match

Rules have priorities so that more specific rules win.

Examples:

* Any merchant containing “UBER” → Transport
* Any merchant containing “DOORDASH” → Dining
* Merchants matching regex “^AMZN|AMAZON” → Shopping

Rules can be added directly in SQLite and re-applied later without re-ingesting CSVs.

---

## ANALYTICS AND VISUALIZATION

Analytics are performed by querying SQLite views.

Current outputs include:

* Monthly total spending bar chart
* Monthly stacked bar chart by category
* Hoverable tooltips showing exact dollar amounts

Charts are rendered using Plotly and open in a browser window. Categories are stacked with the largest spend categories at the bottom for readability.

To run analytics:
./venv/bin/python analytics_sqlite.py

---

## AI YEARLY SPENDING AGENT

The AI agent generates a year-end spending report based entirely on computed metrics from SQLite.

It does NOT:

* Query the database directly
* Perform arithmetic
* Invent numbers

Instead, it receives structured data (totals, categories, months, merchants) and produces an explanatory narrative.

The report includes:

* Executive summary
* Where spending went (top categories)
* Month-by-month observations
* Merchant-level insights
* Budgeting strategies
* Suggested experiments for the next year

Run example:
./venv/bin/python agent_yearly_report.py --year 2025 --out reports/2025.txt

This typically runs in about 1–2 seconds, with most time spent waiting for the AI response.

---

## DESIGN PRINCIPLES

Key design decisions in this project:

* SQLite as a single source of truth
* Money stored as integer cents (no floating-point drift)
* Deterministic analytics before AI interpretation
* CSV ingestion is idempotent and safe to re-run
* AI is used for interpretation, not calculation

This makes the system reliable, explainable, and extensible.

---

## POSSIBLE NEXT EXTENSIONS

Some natural next steps for this project:

* Reclassification script to re-apply category rules without re-ingestion
* Budgets table with budget-vs-actual analysis
* Recurring transaction and subscription detection
* “Ask my finances” natural-language Q&A agent
* Streamlit dashboard combining charts and AI insights

---

## SUMMARY

This project is a production-style personal finance system that combines structured data storage, analytics, visualization, and AI narration. It is intentionally modular so each part can evolve independently, and it is built to scale from simple personal use to a more polished, portfolio-grade application.

If you want, next I can:

* tailor this README to a public GitHub audience
* write a separate “Architecture Notes” document
* add inline docstrings throughout the codebase
