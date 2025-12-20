# Quant Trading Framework

[![CI](https://github.com/sosahinolcay-tech/quant-trading/actions/workflows/ci.yml/badge.svg)](https://github.com/sosahinolcay-tech/quant-trading/actions)
[![codecov](https://codecov.io/gh/sosahinolcay-tech/quant-trading/branch/main/graph/badge.svg)](https://codecov.io/gh/sosahinolcay-tech/quant-trading)
[![PyPI version](https://badge.fury.io/py/quant-trading.svg)](https://pypi.org/project/quant-trading/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive event-driven quantitative trading simulator built in Python. This framework includes multiple trading strategies, backtesting engine, risk management, analytics, and performance evaluation tools.

## Features

- **Event-Driven Engine**: Realistic simulation with limit order matching, slippage, and transaction costs
- **Trading Strategies**:
  - Market Maker (Avellaneda model with adaptive quoting)
  - Pairs Trading (rolling OLS with z-score signals)
- **Analytics & Reporting**: Sharpe ratio, drawdown analysis, bootstrap confidence intervals, trade logs
- **Tools**: Parameter sweep optimization, walk-forward analysis, demo scripts
- **Visualization**: Interactive dashboards and Jupyter notebooks for results
- **Testing**: Comprehensive unit and integration tests
- **CI/CD**: Automated testing and deployment pipeline

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone https://github.com/sosahinolcay-tech/quant-trading.git
cd quant-trading
```

2. Create virtual environment and install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run Demos

- **Market Maker Demo**:
```bash
python tools/run_demo.py
```

- **Pairs Trading Demo**:
```bash
python tools/demo_pairs.py
```

- **Interactive Dashboard** (requires Streamlit):
```bash
pip install streamlit matplotlib
streamlit run app/streamlit_app.py
```

- **Jupyter Notebooks**: Open `notebooks/` for interactive analysis

### Run Tests

```bash
pytest
```

## Project Structure

```
quant-trading/
├── qt/                          # Core framework
│   ├── engine/                  # Simulation engine
│   ├── strategies/              # Trading strategies
│   ├── risk/                    # Risk management
│   ├── analytics/               # Performance analytics
│   └── utils/                   # Utilities
├── tools/                       # Demo and analysis scripts
├── tests/                       # Unit and integration tests
├── notebooks/                   # Jupyter notebooks
├── app/                         # Streamlit dashboard
└── docs/                        # Documentation
```

## Strategies

### Market Maker
Implements the Avellaneda & Stoikov model with:
- EWMA volatility estimation
- Inventory risk management
- Adaptive bid-ask spreads

### Pairs Trading
Statistical arbitrage strategy with:
- Rolling OLS regression
- Z-score based entry/exit signals
- Cointegration testing

## Analytics

- **Performance Metrics**: Sharpe ratio, maximum drawdown, returns
- **Statistical Tests**: Augmented Dickey-Fuller for stationarity
- **Confidence Intervals**: Bootstrap resampling for Sharpe ratio
- **Walk-Forward Analysis**: Out-of-sample validation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure CI passes
5. Submit a pull request

## License

See LICENSE file for details.
