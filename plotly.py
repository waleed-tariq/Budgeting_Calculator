import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def plot_monthly_spend_plotly(monthly_df: pd.DataFrame) -> None:
    """
    Interactive bar chart: total spend per month.
    Expects columns: month, total_spend (Decimal or numeric)
    """
    df = monthly_df.copy()
    df["total_spend"] = df["total_spend"].astype(float)  # Decimal -> float for plotting

    fig = px.bar(
        df,
        x="month",
        y="total_spend",
        hover_data={"month": True, "total_spend": ":$,.2f"},
        title="Monthly Spending",
    )

    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Total Spend ($)",
        yaxis_tickprefix="$",
        yaxis_tickformat=",.2f",
        hovermode="x",
        margin=dict(t=60, r=30, b=60, l=60),
    )

    fig.show()


def plot_monthly_category_breakdown_plotly(breakdown_df: pd.DataFrame) -> None:
    """
    Interactive stacked bar chart: spend by category per month.
    Hover shows month + category + spend.
    Expects columns: month, category, spend (Decimal or numeric)
    """
    df = breakdown_df.copy()
    df["category"] = df["category"].astype(str).str.strip()
    df["spend"] = df["spend"].astype(float)  # Decimal -> float for plotting

    # Aggregate just in case (month, category) appears more than once
    df = (
        df.groupby(["month", "category"], as_index=False)
          .agg(spend=("spend", "sum"))
    )

    # Order categories so biggest spenders are at the bottom of the stack
    cat_order = (
        df.groupby("category")["spend"]
          .sum()
          .sort_values(ascending=False)
          .index
          .tolist()
    )
    df["category"] = pd.Categorical(df["category"], categories=cat_order, ordered=True)

    fig = px.bar(
        df,
        x="month",
        y="spend",
        color="category",
        barmode="stack",
        title="Monthly Spending by Category (Hover for details)",
        hover_data={"month": True, "category": True, "spend": ":$,.2f"},
    )

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Spend ($)",
        yaxis_tickprefix="$",
        yaxis_tickformat=",.2f",
        hovermode="x",
        legend_title_text="Category",
        margin=dict(t=60, r=30, b=60, l=60),
    )

    fig.show()
