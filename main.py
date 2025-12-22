import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
from pathlib import Path
from decimal import Decimal
import plotly.express as px
import plotly.graph_objects as go
from plotly import plot_monthly_spend_plotly, plot_monthly_category_breakdown_plotly


def load_chase_statement(csv_path: str, card_name: str | None = None) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    expected_cols = {
        "Transaction Date",
        "Post Date",
        "Description",
        "Category",
        "Type",
        "Amount",
        "Memo",
    }
    missing = expected_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    df["transaction_date"] = pd.to_datetime(df["Transaction Date"])
    df["post_date"] = pd.to_datetime(df["Post Date"])

    df["amount"] = df["Amount"].apply(lambda x: Decimal(str(x)))

    df["merchant"] = df["Description"].astype(str).str.upper().str.strip()
    df["category"] = df["Category"].fillna("Uncategorized").astype(str).str.strip()

    # Derived fields
    df["month"] = df["transaction_date"].dt.to_period("M").astype(str)
    df["year"] = df["transaction_date"].dt.year
    df["is_credit"] = df["amount"] > 0

    if card_name:
        df["card"] = card_name

    # Optional: normalize Type
    df["type"] = df["Type"].astype(str).str.strip()

    # Keep only useful columns (you can add more back if you want)
    cols = [
        "transaction_date",
        "post_date",
        "month",
        "merchant",
        "category",
        "type",
        "amount",
        "is_credit",
        "Memo",
    ]
    if card_name:
        cols.append("card")

    return df[cols]


def monthly_spend_summary(
    txns: pd.DataFrame,
    include_credits: bool = False
) -> pd.DataFrame:
    """
    Monthly rollup. By default, counts only spending (debits),
    excluding payments/refunds/credits.
    """
    df = txns.copy()

    if not include_credits:
        df = df[df["amount"] < 0]

    summary = (
        df.groupby("month", as_index=False)
          .agg(
              total_spend=("amount", lambda s: sum(s) * Decimal('-1')),  # make positive
              txn_count=("amount", "size"),
          )
          .sort_values("month")
    )
    # Calculate average cost per transaction
    summary["avg_per_transaction"] = summary.apply(
        lambda row: row["total_spend"] / row["txn_count"], axis=1
    )
    return summary


def monthly_category_breakdown(txns: pd.DataFrame, top_n: int | None = None) -> pd.DataFrame:
    df = txns[txns["amount"] < 0].copy()

    breakdown = (
        df.groupby(["month", "category"], as_index=False)
          .agg(
              spend=("amount", lambda s: sum(s) * Decimal('-1')),
              txn_count=("amount", "size"),
          )
          .sort_values(["month", "spend"], ascending=[True, False])
    )

    # Calculate average spending per transaction
    breakdown["avg_per_transaction"] = breakdown.apply(
        lambda row: row["spend"] / row["txn_count"], axis=1
    )

    if top_n is None:
        return breakdown

    # Rank categories within each month by spend
    breakdown["rank_in_month"] = breakdown.groupby("month")["spend"].rank(
        method="first", ascending=False
    )

    top = breakdown[breakdown["rank_in_month"] <= top_n].copy()
    rest = breakdown[breakdown["rank_in_month"] > top_n].copy()

    if not rest.empty:
        other = (
            rest.groupby("month", as_index=False)
                .agg(
                    spend=("spend", lambda s: sum(s)),
                    txn_count=("txn_count", "sum")
                )
        )
        other["category"] = "Other"
        # Calculate average for "Other" category
        other["avg_per_transaction"] = other.apply(
            lambda row: row["spend"] / row["txn_count"], axis=1
        )
        top = pd.concat([top.drop(columns=["rank_in_month"]), other], ignore_index=True)
    else:
        top = top.drop(columns=["rank_in_month"])

    return top.sort_values(["month", "spend"], ascending=[True, False]).reset_index(drop=True)


def save_df(df: pd.DataFrame, output_path: str) -> None:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

def format_money_columns(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """
    Format monetary columns to two decimal places.
    Uses Decimal.quantize for precise rounding.
    """
    from decimal import ROUND_HALF_UP
    df = df.copy()
    for col in cols:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: Decimal(str(x)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                if isinstance(x, (Decimal, int, float)) else x
            )
    return df


# def plot_monthly_spend_plotly(monthly_df: pd.DataFrame) -> None:
#     """
#     Interactive bar chart: total spend per month.
#     Expects columns: month, total_spend (Decimal or numeric)
#     """
#     df = monthly_df.copy()
#     df["total_spend"] = df["total_spend"].astype(float)  # Decimal -> float for plotting

#     fig = px.bar(
#         df,
#         x="month",
#         y="total_spend",
#         hover_data={"month": True, "total_spend": ":$,.2f"},
#         title="Monthly Spending",
#     )

#     fig.update_traces(textposition="outside", cliponaxis=False)
#     fig.update_layout(
#         xaxis_title="Month",
#         yaxis_title="Total Spend ($)",
#         yaxis_tickprefix="$",
#         yaxis_tickformat=",.2f",
#         hovermode="x",
#         margin=dict(t=60, r=30, b=60, l=60),
#     )

#     fig.show()


# def plot_monthly_category_breakdown_plotly(breakdown_df: pd.DataFrame) -> None:
#     """
#     Interactive stacked bar chart: spend by category per month.
#     Hover shows month + category + spend.
#     Expects columns: month, category, spend (Decimal or numeric)
#     """
#     df = breakdown_df.copy()
#     df["category"] = df["category"].astype(str).str.strip()
#     df["spend"] = df["spend"].astype(float)  # Decimal -> float for plotting

#     # Aggregate just in case (month, category) appears more than once
#     df = (
#         df.groupby(["month", "category"], as_index=False)
#           .agg(spend=("spend", "sum"))
#     )

#     # Order categories so biggest spenders are at the bottom of the stack
#     cat_order = (
#         df.groupby("category")["spend"]
#           .sum()
#           .sort_values(ascending=False)
#           .index
#           .tolist()
#     )
#     df["category"] = pd.Categorical(df["category"], categories=cat_order, ordered=True)

#     fig = px.bar(
#         df,
#         x="month",
#         y="spend",
#         color="category",
#         barmode="stack",
#         title="Monthly Spending by Category (Hover for details)",
#         hover_data={"month": True, "category": True, "spend": ":$,.2f"},
#     )

#     fig.update_layout(
#         xaxis_title="Month",
#         yaxis_title="Spend ($)",
#         yaxis_tickprefix="$",
#         yaxis_tickformat=",.2f",
#         hovermode="x",
#         legend_title_text="Category",
#         margin=dict(t=60, r=30, b=60, l=60),
#     )

#     fig.show()




if __name__ == "__main__":
    input_csv = "data/chase_statement.csv"

    txns = load_chase_statement(input_csv, card_name="Chase Card")

    monthly = monthly_spend_summary(txns, include_credits=False)
    breakdown = monthly_category_breakdown(txns, top_n=10)

    # 🔹 Round money columns
    txns = format_money_columns(txns, ["amount"])
    monthly = format_money_columns(monthly, ["total_spend", "avg_per_transaction"])
    breakdown = format_money_columns(breakdown, ["spend", "avg_per_transaction"])

    conn = sqlite3.connect("budget.db")

    monthly = pd.read_sql("SELECT * FROM v_monthly_summary", conn)
    category = pd.read_sql("SELECT * FROM v_monthly_category_breakdown", conn)

    plot_monthly_spend_plotly(monthly)
    plot_monthly_category_breakdown_plotly(breakdown)

    save_df(txns, "output/transactions_clean.csv")
    save_df(monthly, "output/monthly_summary.csv")
    save_df(breakdown, "output/monthly_category_breakdown.csv")

