import sqlite3
import pandas as pd

from main import plot_monthly_spend_plotly, plot_monthly_category_breakdown_plotly

DB_PATH = "budget.db"

def main():
    conn = sqlite3.connect(DB_PATH)

    monthly = pd.read_sql("SELECT * FROM v_monthly_summary ORDER BY month", conn)
    category = pd.read_sql("SELECT * FROM v_monthly_category ORDER BY month, spend DESC", conn)

    conn.close()

    plot_monthly_spend_plotly(monthly)
    plot_monthly_category_breakdown_plotly(category)

if __name__ == "__main__":
    main()
