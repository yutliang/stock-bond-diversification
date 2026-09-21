"""Build the project's small SQLite data layer from its existing sources."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

try:
    import yfinance as yf
except ImportError as exc:
    raise SystemExit(
        "Missing dependency 'yfinance'. Install it with: python -m pip install yfinance"
    ) from exc


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
DATABASE_PATH = PROJECT_ROOT / "data" / "processed" / "portfolio.db"
SCHEMA_PATH = PROJECT_ROOT / "sql" / "schema.sql"
ANALYSIS_QUERIES_PATH = PROJECT_ROOT / "sql" / "analysis_queries.sql"

HICP_PATH = RAW_DATA_DIR / "ECB Data Portal_20260817160023.csv"
ECB_RATE_PATH = RAW_DATA_DIR / "ECB Data Portal_20260818182339.csv"

MARKET_START = "2018-01-01"
MARKET_END = "2026-08-01"  # yfinance treats end as exclusive.

ASSETS = {
    "IMAE.AS": "stock",
    "IBGM.AS": "bond",
    "X710.DE": "alternative_bond",
}


def download_asset_prices() -> pd.DataFrame:
    """Download the adjusted closing prices used by the existing notebook."""
    frames: list[pd.DataFrame] = []

    for ticker, asset_class in ASSETS.items():
        market_data = yf.download(
            ticker,
            start=MARKET_START,
            end=MARKET_END,
            auto_adjust=True,
            progress=False,
        )
        if market_data.empty:
            raise RuntimeError(f"Yahoo Finance returned no data for {ticker}.")

        close = market_data["Close"]
        if isinstance(close, pd.DataFrame):
            if close.shape[1] != 1:
                raise RuntimeError(f"Unexpected Close columns for {ticker}.")
            close = close.iloc[:, 0]

        frame = close.rename("adjusted_close").reset_index()
        frame = frame.rename(columns={frame.columns[0]: "trade_date"})
        frame["trade_date"] = pd.to_datetime(frame["trade_date"]).dt.strftime(
            "%Y-%m-%d"
        )
        frame["ticker"] = ticker
        frame["asset_class"] = asset_class
        frames.append(
            frame[["trade_date", "ticker", "asset_class", "adjusted_close"]]
        )

    prices = pd.concat(frames, ignore_index=True)
    prices["adjusted_close"] = pd.to_numeric(
        prices["adjusted_close"], errors="raise"
    )
    return prices


def load_ecb_csv(path: Path, value_name: str) -> pd.DataFrame:
    """Read an ECB export, retaining its date and numeric observation value."""
    source = pd.read_csv(path)
    if source.shape[1] < 3:
        raise ValueError(f"Expected at least three columns in {path.name}.")

    data = source.iloc[:, [0, 2]].copy()
    data.columns = ["observation_date", value_name]
    data["observation_date"] = pd.to_datetime(
        data["observation_date"], errors="raise"
    ).dt.strftime("%Y-%m-%d")
    data[value_name] = pd.to_numeric(data[value_name], errors="coerce")
    data = data.dropna(subset=[value_name])
    return data


def validate_source_data(
    prices: pd.DataFrame,
    hicp: pd.DataFrame,
    ecb_rates: pd.DataFrame,
) -> None:
    """Fail before writing if keys or required values are invalid."""
    checks = [
        (prices, ["trade_date", "ticker"], "asset_prices"),
        (hicp, ["observation_date"], "hicp_monthly"),
        (ecb_rates, ["observation_date"], "ecb_rates"),
    ]
    for frame, key, name in checks:
        if frame.empty:
            raise ValueError(f"{name} contains no rows.")
        if frame.duplicated(key).any():
            raise ValueError(f"{name} contains duplicate primary keys.")
        if frame.isna().any().any():
            raise ValueError(f"{name} contains missing required values.")


def build_database() -> None:
    """Create a fresh database and replace the previous generated file."""
    prices = download_asset_prices()
    hicp = load_ecb_csv(HICP_PATH, "inflation_rate")
    ecb_rates = load_ecb_csv(ECB_RATE_PATH, "deposit_rate")
    validate_source_data(prices, hicp, ecb_rates)

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = DATABASE_PATH.with_suffix(".db.tmp")
    if temporary_path.exists():
        temporary_path.unlink()

    try:
        connection = sqlite3.connect(temporary_path)
        try:
            connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
            prices.to_sql("asset_prices", connection, if_exists="append", index=False)
            hicp.to_sql("hicp_monthly", connection, if_exists="append", index=False)
            ecb_rates.to_sql("ecb_rates", connection, if_exists="append", index=False)
            connection.executescript(
                ANALYSIS_QUERIES_PATH.read_text(encoding="utf-8")
            )
            connection.execute("PRAGMA optimize")
            connection.commit()
        finally:
            connection.close()
        temporary_path.replace(DATABASE_PATH)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()

    print(f"Created {DATABASE_PATH.relative_to(PROJECT_ROOT)}")
    with sqlite3.connect(DATABASE_PATH) as connection:
        for table, date_column in (
            ("asset_prices", "trade_date"),
            ("hicp_monthly", "observation_date"),
            ("ecb_rates", "observation_date"),
        ):
            row = connection.execute(
                f"""
                SELECT COUNT(*), MIN({date_column}), MAX({date_column})
                FROM {table}
                """
            ).fetchone()
            print(f"{table}: rows={row[0]}, dates={row[1]} to {row[2]}")
        analysis_row = connection.execute(
            """
            SELECT COUNT(*), MIN(trade_date), MAX(trade_date)
            FROM daily_analysis
            """
        ).fetchone()
        print(
            "daily_analysis: "
            f"rows={analysis_row[0]}, "
            f"dates={analysis_row[1]} to {analysis_row[2]}"
        )


if __name__ == "__main__":
    build_database()
