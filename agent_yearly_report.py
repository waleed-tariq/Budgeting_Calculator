import os
import sqlite3
from dataclasses import dataclass
from typing import Any, Dict, List

import pandas as pd

# If you're using OpenAI API:
from openai import OpenAI  # official SDK
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@dataclass
class YearContext:
    year: int
    currency: str = "USD"


def load_year_metrics(db_path: str, year: int) -> Dict[str, Any]:
    conn = sqlite3.connect(db_path)

    # Only spending (amount_cents < 0). Stored as negative cents; convert to positive dollars in queries.
    total = pd.read_sql(
        """
        SELECT
          SUM(CASE WHEN amount_cents < 0 THEN -amount_cents ELSE 0 END) AS spend_cents,
          COUNT(*) AS txn_count
        FROM transactions
        WHERE substr(transaction_date, 1, 4) = ?
        """,
        conn,
        params=(str(year),),
    ).iloc[0].to_dict()

    by_month = pd.read_sql(
        """
        SELECT
          substr(transaction_date, 1, 7) AS month,
          SUM(CASE WHEN amount_cents < 0 THEN -amount_cents ELSE 0 END) AS spend_cents
        FROM transactions
        WHERE substr(transaction_date, 1, 4) = ?
        GROUP BY month
        ORDER BY month
        """,
        conn,
        params=(str(year),),
    )

    by_category = pd.read_sql(
        """
        SELECT
          COALESCE(category_final, category_chase, 'Uncategorized') AS category,
          SUM(CASE WHEN amount_cents < 0 THEN -amount_cents ELSE 0 END) AS spend_cents
        FROM transactions
        WHERE substr(transaction_date, 1, 4) = ?
        GROUP BY category
        ORDER BY spend_cents DESC
        """,
        conn,
        params=(str(year),),
    )

    by_merchant = pd.read_sql(
        """
        SELECT
          m.name AS merchant,
          SUM(CASE WHEN t.amount_cents < 0 THEN -t.amount_cents ELSE 0 END) AS spend_cents
        FROM transactions t
        JOIN merchants m ON t.merchant_id = m.id
        WHERE substr(t.transaction_date, 1, 4) = ?
        GROUP BY m.name
        ORDER BY spend_cents DESC
        LIMIT 15
        """,
        conn,
        params=(str(year),),
    )

    conn.close()

    # Convert to dollars (float for reporting only)
    def cents_to_dollars(df: pd.DataFrame, col: str) -> pd.DataFrame:
        out = df.copy()
        out[col] = (out[col] / 100.0).round(2)
        return out

    total_spend = round((total["spend_cents"] or 0) / 100.0, 2)

    return {
        "year": year,
        "total_spend": total_spend,
        "txn_count": int(total["txn_count"] or 0),
        "by_month": cents_to_dollars(by_month, "spend_cents").rename(columns={"spend_cents": "spend"}),
        "by_category": cents_to_dollars(by_category, "spend_cents").rename(columns={"spend_cents": "spend"}),
        "top_merchants": cents_to_dollars(by_merchant, "spend_cents").rename(columns={"spend_cents": "spend"}),
    }

def build_prompt(metrics: Dict[str, Any]) -> str:
    by_month = metrics["by_month"].to_dict(orient="records")
    by_category = metrics["by_category"].head(12).to_dict(orient="records")
    top_merchants = metrics["top_merchants"].to_dict(orient="records")

    return f"""
You are a personal finance analyst.

Write a concise but insightful YEAR-END SPENDING REPORT for {metrics["year"]}.
Rules:
- Use ONLY the numbers provided. Do not invent numbers.
- Make budgeting advice specific and measurable.
- Call out the top 5 categories and their shares where possible.
- Mention notable monthly spikes.
- Output in the format below exactly.

DATA:
Total spend: ${metrics["total_spend"]:,.2f}
Transaction count: {metrics["txn_count"]}

Monthly spend (dollars):
{by_month}

Spend by category (dollars):
{by_category}

Top merchants (dollars):
{top_merchants}

OUTPUT FORMAT:
1) Executive summary (3–5 bullets)
2) Where the money went (top categories + short interpretation)
3) Month-by-month story (spikes, trend, seasonality)
4) Merchant insights (top merchants and what they imply)
5) Budgeting strategies (5 actions, each with a $ target or rule)
6) Next-year experiment plan (3 experiments to try for 30 days)
"""


def generate_year_end_report(metrics: Dict[str, Any]) -> str:
    prompt = build_prompt(metrics)

    response = client.responses.create(
        model="gpt-5",   # choose your preferred model
        input=prompt,
    )

    return response.output_text

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="budget.db")
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--out", default=None, help="Optional path to save report as .md")
    args = parser.parse_args()

    metrics = load_year_metrics(args.db, args.year)
    report = generate_year_end_report(metrics)

    print(report)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report)
