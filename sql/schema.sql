PRAGMA foreign_keys = ON;

CREATE TABLE asset_prices (
    trade_date TEXT NOT NULL,
    ticker TEXT NOT NULL,
    asset_class TEXT NOT NULL CHECK (
        asset_class IN ('stock', 'bond', 'alternative_bond')
    ),
    adjusted_close REAL NOT NULL CHECK (adjusted_close > 0),
    PRIMARY KEY (trade_date, ticker)
);

CREATE INDEX idx_asset_prices_ticker_date
    ON asset_prices (ticker, trade_date);

CREATE TABLE hicp_monthly (
    observation_date TEXT PRIMARY KEY NOT NULL,
    inflation_rate REAL NOT NULL
);

CREATE TABLE ecb_rates (
    observation_date TEXT PRIMARY KEY NOT NULL,
    deposit_rate REAL NOT NULL
);
