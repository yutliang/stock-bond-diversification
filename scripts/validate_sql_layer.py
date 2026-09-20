"""Validate that the SQL transformations match their pandas equivalents."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "data" / "processed" / "portfolio.db"


def load_database_tables() -> tuple[pd.DataFrame, ...]:
    if not DATABASE_PATH.exists():
        raise SystemExit(
            "Database not found. Run: python scripts/build_database.py"
        )

    with sqlite3.connect(DATABASE_PATH) as connection:
        prices = pd.read_sql_query("SELECT * FROM asset_prices", connection)
        hicp = pd.read_sql_query("SELECT * FROM hicp_monthly", connection)
        ecb_rates = pd.read_sql_query("SELECT * FROM ecb_rates", connection)
        sql_daily = pd.read_sql_query(
            "SELECT * FROM daily_analysis ORDER BY trade_date", connection
        )
        sql_annual = pd.read_sql_query(
            "SELECT * FROM annual_summary ORDER BY year", connection
        )
    return prices, hicp, ecb_rates, sql_daily, sql_annual


def build_pandas_equivalent(
    prices: pd.DataFrame,
    hicp: pd.DataFrame,
    ecb_rates: pd.DataFrame,
) -> pd.DataFrame:
    stock_prices = (
        prices.loc[prices["ticker"] == "IMAE.AS"]
        .set_index("trade_date")["adjusted_close"]
        .sort_index()
    )
    bond_prices = (
        prices.loc[prices["ticker"] == "IBGM.AS"]
        .set_index("trade_date")["adjusted_close"]
        .sort_index()
    )

    daily = pd.concat(
        [
            stock_prices.pct_change(fill_method=None).rename("stock_return"),
            bond_prices.pct_change(fill_method=None).rename("bond_return"),
        ],
        axis=1,
        join="inner",
    ).dropna()
    daily["portfolio_60_40_return"] = (
        0.6 * daily["stock_return"] + 0.4 * daily["bond_return"]
    )

    inflation_by_month = hicp.assign(
        month=hicp["observation_date"].str[:7]
    ).set_index("month")["inflation_rate"]
    daily["inflation_rate"] = daily.index.str[:7].map(inflation_by_month)

    rates_by_date = ecb_rates.set_index("observation_date")["deposit_rate"]
    daily["ecb_rate"] = daily.index.map(rates_by_date)
    daily["ecb_rate_change"] = daily["ecb_rate"].diff()
    daily["high_inflation"] = (daily["inflation_rate"] > 5.0).astype(int)
    daily["hiking_regime"] = (
        (daily.index >= "2022-07-27") & (daily.index <= "2023-09-20")
    ).astype(int)
    return daily.reset_index(names="trade_date")


def validate() -> None:
    prices, hicp, ecb_rates, sql_daily, sql_annual = load_database_tables()
    pandas_daily = build_pandas_equivalent(prices, hicp, ecb_rates)

    if not sql_daily["trade_date"].equals(pandas_daily["trade_date"]):
        raise AssertionError("SQL and pandas trading dates differ.")

    numeric_columns = [
        "stock_return",
        "bond_return",
        "portfolio_60_40_return",
        "inflation_rate",
        "ecb_rate",
        "ecb_rate_change",
    ]
    for column in numeric_columns:
        np.testing.assert_allclose(
            sql_daily[column],
            pandas_daily[column],
            rtol=1e-12,
            atol=1e-12,
            equal_nan=True,
            err_msg=f"SQL and pandas differ for {column}.",
        )

    for column in ["high_inflation", "hiking_regime"]:
        if not sql_daily[column].equals(pandas_daily[column]):
            raise AssertionError(f"SQL and pandas differ for {column}.")

    required_columns = [
        "stock_return",
        "bond_return",
        "portfolio_60_40_return",
        "inflation_rate",
        "ecb_rate",
    ]
    missing = sql_daily[required_columns].isna().sum()
    if missing.any():
        raise AssertionError(f"Unexpected missing values:\n{missing[missing > 0]}")

    boundary_flags = sql_daily.set_index("trade_date")["hiking_regime"]
    expected_flags = {
        "2022-07-26": 0,
        "2022-07-27": 1,
        "2023-09-20": 1,
        "2023-09-21": 0,
    }
    for date, expected in expected_flags.items():
        actual = int(boundary_flags.loc[date])
        if actual != expected:
            raise AssertionError(
                f"Unexpected hiking_regime on {date}: {actual}"
            )

    pandas_annual = pandas_daily.assign(
        year=pandas_daily["trade_date"].str[:4]
    ).groupby("year", as_index=False).agg(
        trading_days=("trade_date", "size"),
        avg_stock_return=("stock_return", "mean"),
        avg_bond_return=("bond_return", "mean"),
        avg_portfolio_return=("portfolio_60_40_return", "mean"),
        avg_inflation=("inflation_rate", "mean"),
        min_ecb_rate=("ecb_rate", "min"),
        max_ecb_rate=("ecb_rate", "max"),
    )
    if not sql_annual[["year", "trading_days"]].equals(
        pandas_annual[["year", "trading_days"]]
    ):
        raise AssertionError("SQL and pandas annual groups differ.")
    for column in sql_annual.columns[2:]:
        np.testing.assert_allclose(
            sql_annual[column],
            pandas_annual[column],
            rtol=1e-12,
            atol=1e-12,
            err_msg=f"SQL and pandas annual summaries differ for {column}.",
        )

    print("SQL layer validation passed.")
    print(
        f"daily_analysis: {len(sql_daily)} rows, "
        f"{sql_daily['trade_date'].min()} to {sql_daily['trade_date'].max()}"
    )
    print(f"annual_summary: {len(sql_annual)} yearly groups")
    print("Unexpected missing required values: 0")
    print("Maximum numeric difference versus pandas: below 1e-12")


if __name__ == "__main__":
    validate()
