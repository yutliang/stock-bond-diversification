CREATE VIEW daily_asset_returns AS
WITH prices_with_previous AS (
    SELECT
        trade_date,
        ticker,
        asset_class,
        adjusted_close,
        LAG(adjusted_close) OVER (
            PARTITION BY ticker
            ORDER BY trade_date
        ) AS previous_close
    FROM asset_prices
)
SELECT
    trade_date,
    ticker,
    asset_class,
    adjusted_close,
    previous_close,
    adjusted_close / previous_close - 1.0 AS daily_return
FROM prices_with_previous;


CREATE VIEW daily_analysis AS
WITH stock_returns AS (
    SELECT trade_date, daily_return AS stock_return
    FROM daily_asset_returns
    WHERE ticker = 'IMAE.AS'
      AND daily_return IS NOT NULL
),
bond_returns AS (
    SELECT trade_date, daily_return AS bond_return
    FROM daily_asset_returns
    WHERE ticker = 'IBGM.AS'
      AND daily_return IS NOT NULL
),
stock_bond_returns AS (
    SELECT
        stock.trade_date,
        stock.stock_return,
        bond.bond_return
    FROM stock_returns AS stock
    INNER JOIN bond_returns AS bond
        ON stock.trade_date = bond.trade_date
),
enriched_returns AS (
    SELECT
        market.trade_date,
        market.stock_return,
        market.bond_return,
        0.6 * market.stock_return
            + 0.4 * market.bond_return AS portfolio_60_40_return,
        hicp.inflation_rate,
        ecb.deposit_rate AS ecb_rate,
        CASE
            WHEN hicp.inflation_rate > 5.0 THEN 1
            ELSE 0
        END AS high_inflation,
        CASE
            WHEN market.trade_date BETWEEN '2022-07-27' AND '2023-09-20'
                THEN 1
            ELSE 0
        END AS hiking_regime
    FROM stock_bond_returns AS market
    LEFT JOIN hicp_monthly AS hicp
        ON strftime('%Y-%m', market.trade_date)
         = strftime('%Y-%m', hicp.observation_date)
    LEFT JOIN ecb_rates AS ecb
        ON market.trade_date = ecb.observation_date
)
SELECT
    trade_date,
    stock_return,
    bond_return,
    portfolio_60_40_return,
    inflation_rate,
    ecb_rate,
    ecb_rate - LAG(ecb_rate) OVER (
        ORDER BY trade_date
    ) AS ecb_rate_change,
    high_inflation,
    hiking_regime
FROM enriched_returns;


CREATE VIEW annual_summary AS
SELECT
    strftime('%Y', trade_date) AS year,
    COUNT(*) AS trading_days,
    AVG(stock_return) AS avg_stock_return,
    AVG(bond_return) AS avg_bond_return,
    AVG(portfolio_60_40_return) AS avg_portfolio_return,
    AVG(inflation_rate) AS avg_inflation,
    MIN(ecb_rate) AS min_ecb_rate,
    MAX(ecb_rate) AS max_ecb_rate
FROM daily_analysis
GROUP BY strftime('%Y', trade_date)
ORDER BY year;
