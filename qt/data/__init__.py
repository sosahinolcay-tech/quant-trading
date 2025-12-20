"""Data sources for real market data"""
from typing import List, Tuple, Optional
import pandas as pd
import numpy as np


class DataSource:
    """Base class for data sources"""

    def get_prices(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """Get historical price data for symbol"""
        raise NotImplementedError


class YahooFinanceDataSource(DataSource):
    """Yahoo Finance data source using yfinance"""

    def get_prices(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date)
            if df.empty:
                return None
            # Convert to our format: timestamp, price
            df = df[['Close']].rename(columns={'Close': 'price'})
            df['timestamp'] = df.index.astype(np.int64) // 10**9  # Unix timestamp
            return df[['timestamp', 'price']]
        except Exception:
            return None


class SyntheticDataSource(DataSource):
    """Synthetic data generator (existing functionality)"""

    def get_prices(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Generate synthetic price series"""
        np.random.seed(hash(symbol) % 2**32)  # Deterministic seed per symbol

        # Parse dates
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        days = (end - start).days

        if days <= 0:
            days = 252  # Default to 1 year

        # Generate random walk
        timestamps = pd.date_range(start=start, periods=days, freq='D')
        prices = [100.0]  # Start price

        for _ in range(len(timestamps) - 1):
            ret = np.random.normal(0, 0.02)  # 2% daily vol
            new_price = prices[-1] * (1 + ret)
            prices.append(max(new_price, 0.01))  # Floor at 0.01

        df = pd.DataFrame({
            'timestamp': timestamps.astype(np.int64) // 10**9,
            'price': prices
        })

        return df


def get_data_source(source_type: str = "synthetic") -> DataSource:
    """Factory for data sources"""
    if source_type == "yahoo":
        return YahooFinanceDataSource()
    else:
        return SyntheticDataSource()