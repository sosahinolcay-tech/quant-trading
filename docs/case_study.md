# Case Study: Market Making & Pairs Trading

This document summarizes the strategies, methodology, results, and limitations.

## Motivation

This project implements a lightweight backtesting framework for quantitative trading strategies, focusing on market making and pairs trading. The goal is to demonstrate strategy implementation, risk management, and performance evaluation in a simulated environment.

## Data and Assumptions

- **Data**: Synthetic cointegrated price series generated using NumPy random walks.
- **Assumptions**:
  - No transaction costs beyond configurable fees and slippage.
  - Immediate execution for market orders, limit orders rest in order book.
  - Perfect liquidity for market orders with slippage modeling.
  - Daily returns assumption for Sharpe ratio (252 trading days).

## Strategy Design

### Market Making (Avellaneda-Stoikov Approximation)

- **Core Idea**: Dynamically quote bid/ask spreads based on inventory and volatility.
- **Key Components**:
  - EWMA volatility estimation.
  - Reservation price adjustment for inventory control.
  - Adaptive quoting intervals to reduce churn.
  - Safety limits on inventory and spread.
- **Parameters**: risk_aversion, max_inventory, ewma_alpha, min_quote_interval.

### Pairs Trading

- **Core Idea**: Exploit mean-reversion in cointegrated asset pairs.
- **Key Components**:
  - Rolling OLS to estimate hedge ratio (beta).
  - Z-score of spread for entry/exit signals.
  - Position sizing based on beta.
- **Parameters**: window (lookback), entry_z, exit_z, quantity.

## Results and Statistical Validation

### Market Making Demo
- Sharpe Ratio: ~0.0 (flat in synthetic data, but framework validates).
- Trades: Variable based on parameters.
- Inventory boundedness confirmed in tests.

### Pairs Trading Demo
- Sharpe Ratio: ~-2.6 (negative due to synthetic data characteristics).
- Trades: 104 in demo run.
- Turnover: ~166k.

### Walk-Forward Analysis
- 5 windows with varying beta.
- Average Sharpe: 0.0 (no trades triggered in short windows).
- Demonstrates framework for out-of-sample testing.

## Limitations and Next Steps

- **Limitations**:
  - Synthetic data may not capture real market dynamics.
  - No real-time execution or live trading integration.
  - Simplified execution model.
- **Next Steps**:
  - Integrate real market data.
  - Add more strategies (e.g., momentum, mean-reversion).
  - Implement portfolio optimization.
  - Enhance dashboard with interactive plots.
