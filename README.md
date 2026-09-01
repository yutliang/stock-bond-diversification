# When Bonds Stop Diversifying

*Stress Testing Stock–Bond Diversification under Inflation and Interest-Rate Shocks*

## Project Overview

Traditional 60/40 portfolios rely on government bonds to reduce equity downside risk. This project examines when that diversification benefit weakens and whether stock–bond correlation alone is sufficient to explain the deterioration.

Using a European stock–bond portfolio from January 2018 to July 2026, the analysis combines daily ETF market data with euro-area HICP inflation and ECB policy-rate data.

The central finding is that the weak diversification observed in 2022 was not primarily driven by unusually high stock–bond correlation. Instead, the bond sleeve itself became materially riskier and contributed far more to total portfolio risk.

## Key Finding

The 2020–2022 comparison provides the central empirical result:

| Metric | 2020 | 2022 |
|---|---:|---:|
| Stock–Bond Correlation | 0.30 | 0.12 |
| Stock Max Drawdown | -35.60% | -19.44% |
| Bond Max Drawdown | -7.29% | -20.29% |
| 60/40 Protection | 10.63 pp | 0.81 pp |

Despite higher stock–bond correlation in 2020, the 60/40 portfolio provided substantially stronger downside protection.

The key difference was the bond sleeve:

- Bond volatility increased from **6.34% to 10.69%**
- Bond maximum drawdown deteriorated from **-7.29% to -20.29%**
- Bond variance contribution increased from **2.0% to 11.7%**

This suggests that diversification effectiveness depends not only on co-movement, but also on whether the bond allocation retains its defensive characteristics.

## Research Approach

The analysis follows a structured progression from descriptive evidence to portfolio-risk diagnosis and forward-looking stress testing:

1. **Dynamic diversification**
   - Full-sample and 60-day rolling stock–bond correlation
   - 120-day rolling correlation as a robustness check

2. **Macro-regime analysis**
   - Euro-area HICP inflation thresholds of 4%, 5%, and 6%
   - ECB hiking versus non-hiking regimes
   - Interaction regression with HAC standard errors

3. **Portfolio-risk diagnosis**
   - Year-specific maximum drawdown
   - Volatility and portfolio-variance decomposition
   - Historical VaR and Expected Shortfall

4. **Stress testing**
   - 2020 Growth Shock versus 2022 Inflation / Rate Shock
   - Forward-looking joint equity–bond shock scenarios
   - Bond Stress Ratio as a measure of diversification vulnerability

## Core Figures

### Time-Varying Stock–Bond Correlation

![60-Day Rolling Stock–Bond Correlation](figures/rolling_correlation.png)

### 2020 vs 2022 Drawdown Dynamics

![Drawdown Dynamics](figures/drawdown_comparison.png)

### Forward-Looking Diversification Stress

![Diversification Protection Heatmap](figures/diversification_protection_heatmap.png)

## Robustness

The main conclusions remain qualitatively unchanged when:

- using a 120-day instead of a 60-day rolling-correlation window;
- changing the high-inflation threshold across 4%, 5%, and 6%;
- replacing the primary bond ETF with `X710.DE`.

## Risk Management Implication

The results suggest that diversification monitoring should combine three dimensions:

- **Co-movement risk** — stock–bond correlation and covariance;
- **Bond standalone risk** — volatility, drawdown, tail risk, and variance contribution;
- **Relative stress severity** — bond stress relative to equity stress.

A low stock–bond correlation does not necessarily imply strong diversification if the bond sleeve itself becomes a material source of risk.

## Repository Structure

```text
stock_bond_diversification/
├── data/
├── figures/
├── notebooks/
│   └── 01_market_data.ipynb
├── summary/
│   └── final_synthesis.md
└── README.md
```

## Tools and Data

- Python
- pandas
- NumPy
- matplotlib
- statsmodels
- Yahoo Finance market data
- ECB Data Portal
- Euro-area HICP inflation
- ECB policy-rate data

## Full Research Note

For the complete methodology, empirical results, robustness checks, stress-testing framework, and limitations, see:

`summary/final_synthesis.md`