from datetime import date

import numpy as np
import pandas as pd
import streamlit as st

from qt.analytics.metrics import (
    compute_cagr,
    compute_calmar,
    compute_drawdown,
    compute_drawdown_duration,
    compute_return_stats,
    compute_returns,
    compute_sharpe,
    compute_sortino,
    rolling_sharpe,
    rolling_volatility,
)
from qt.analytics.risk import stress_test_equity, monte_carlo_horizon_var, compute_var, compute_cvar
from qt.analytics.risk_ext import multi_asset_monte_carlo_var, bootstrap_var, garch_var
from qt.data import get_data_source
from qt.data.prep import prepare_price_frame
from qt.engine.engine import SimulationEngine
from qt.strategies.market_maker import AvellanedaMarketMaker
from qt.strategies.pairs import PairsStrategy

st.set_page_config(page_title="Quant Trading Dashboard", layout="wide")
st.title("Quant Trading Framework Dashboard")


@st.cache_data(show_spinner=False)
def fetch_prices(symbol: str, start_date: str, end_date: str, interval: str, source: str):
    ds = get_data_source(source)
    return ds.get_prices(symbol, start_date, end_date, interval=interval)


def equity_to_df(equity_history):
    if not equity_history:
        return pd.DataFrame(columns=["timestamp", "equity"])
    df = pd.DataFrame(equity_history, columns=["timestamp", "equity"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s", errors="coerce")
    return df


def compute_performance_summary(equity_history):
    equities = [v for (_t, v) in equity_history] if equity_history else []
    rets = compute_returns(equities)
    dd = compute_drawdown(equities)
    stats = compute_return_stats(rets)
    duration = compute_drawdown_duration(equities)
    summary = {
        "sharpe": compute_sharpe(rets),
        "sortino": compute_sortino(rets),
        "cagr": compute_cagr(equities),
        "calmar": compute_calmar(equities),
        "max_drawdown": dd.get("max_drawdown", 0.0),
        "max_drawdown_duration": duration["max_duration"],
        "avg_drawdown_duration": duration["avg_duration"],
        "mean_return": stats["mean"],
        "volatility": stats["std"],
        "skew": stats["skew"],
        "kurtosis": stats["kurtosis"],
    }
    return summary, rets


tabs = st.tabs(["Data Setup", "Strategy Runs", "Analytics & Risk", "Comparison", "Portfolio VaR"])

with tabs[0]:
    st.subheader("Data Setup")
    source = st.selectbox("Primary Data Source", ["yahoo", "synthetic"])
    symbol = st.text_input("Primary Symbol", value="AAPL")
    start = st.date_input("Start Date", value=date(2022, 1, 1))
    end = st.date_input("End Date", value=date(2024, 1, 1))
    interval = st.selectbox("Interval", ["1d", "1h"])

    if st.button("Validate Data", key="validate_data"):
        with st.spinner("Fetching and validating data..."):
            df = fetch_prices(symbol, str(start), str(end), interval, source)
            if df is None or df.empty:
                st.error("No data returned. Check symbol or data source.")
            else:
                prepared, issues = prepare_price_frame(df, min_rows=20)
                if issues:
                    st.warning(f"Validation issues: {issues}")
                st.dataframe(prepared.head(10), use_container_width=True)
                st.line_chart(prepared.set_index("timestamp")["price"], height=250)

with tabs[1]:
    st.subheader("Strategy Runs")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("Market Maker Configuration")
        mm_symbol = st.text_input("Symbol", value="AAPL", key="mm_symbol")
        mm_risk = st.slider("Risk Aversion", 0.01, 1.0, 0.1, 0.01)
        mm_max_inv = st.slider("Max Inventory", 10, 1000, 100)
        if st.button("Run Market Maker", key="run_mm"):
            with st.spinner("Running market maker simulation..."):
                engine = SimulationEngine(execution_fee=0.0005, slippage_coeff=0.0001)
                strat = AvellanedaMarketMaker(
                    symbol=mm_symbol,
                    risk_aversion=mm_risk,
                    max_inventory=mm_max_inv,
                )
                engine.register_strategy(strat)
                engine.run_demo(data_source=source, start_date=str(start), end_date=str(end), interval=interval)
                st.session_state["mm_equity"] = engine.account.equity_history
                st.session_state["mm_trade_log"] = engine.trade_log
                st.success("Market maker simulation completed.")

    with col2:
        st.markdown("Pairs Trading Configuration")
        px = st.text_input("Symbol X", value="MSFT", key="pairs_x")
        py = st.text_input("Symbol Y", value="AAPL", key="pairs_y")
        window = st.slider("Rolling Window", 20, 120, 60)
        entry_z = st.slider("Entry Z-Score", 1.0, 3.5, 1.5, 0.1)
        exit_z = st.slider("Exit Z-Score", 0.1, 1.5, 0.5, 0.1)
        if st.button("Run Pairs Trading", key="run_pairs"):
            with st.spinner("Running pairs trading simulation..."):
                engine = SimulationEngine(execution_fee=0.0005, slippage_coeff=0.0001)
                strat = PairsStrategy(
                    symbol_x=px,
                    symbol_y=py,
                    window=window,
                    entry_z=entry_z,
                    exit_z=exit_z,
                    quantity=10.0,
                )
                engine.register_strategy(strat)
                engine.run_demo(data_source=source, start_date=str(start), end_date=str(end), interval=interval)
                st.session_state["pairs_equity"] = engine.account.equity_history
                st.session_state["pairs_trade_log"] = engine.trade_log
                st.success("Pairs trading simulation completed.")

with tabs[2]:
    st.subheader("Analytics & Risk")
    view = st.radio("Select Strategy", ["Market Maker", "Pairs Trading"], horizontal=True)
    key = "mm_equity" if view == "Market Maker" else "pairs_equity"
    equity_history = st.session_state.get(key, [])
    if not equity_history:
        st.info("Run a strategy to view analytics.")
    else:
        summary, rets = compute_performance_summary(equity_history)
        st.dataframe(pd.DataFrame([summary]), use_container_width=True)

        df_eq = equity_to_df(equity_history)
        st.line_chart(df_eq.set_index("timestamp")["equity"], height=250)

        dd = compute_drawdown([v for (_t, v) in equity_history])
        dd_series = pd.Series(dd.get("drawdown_series", []))
        st.line_chart(dd_series, height=200)

        rolling = rolling_sharpe([v for (_t, v) in equity_history], window=20)
        st.line_chart(pd.Series(rolling), height=200)

        rolling_vol = rolling_volatility(rets, window=20)
        st.line_chart(pd.Series(rolling_vol), height=200)

        if len(rets) > 1:
            var_95 = compute_var(rets, alpha=0.05, method="historical")
            cvar_95 = compute_cvar(rets, alpha=0.05, method="historical")
            mc_var_5d = monte_carlo_horizon_var(rets, alpha=0.05, horizon=5, simulations=5000)
            st.metric("VaR (95%)", f"{var_95:.4f}")
            st.metric("CVaR (95%)", f"{cvar_95:.4f}")
            st.metric("MC VaR 5d (95%)", f"{mc_var_5d:.4f}")
            if st.button("Apply 30% Shock", key="shock_apply"):
                stressed = stress_test_equity([v for (_t, v) in equity_history], shock_pct=-0.3)
                st.line_chart(pd.Series(stressed["stressed_equity"]), height=200)

with tabs[3]:
    st.subheader("Comparison")
    mm_eq = st.session_state.get("mm_equity", [])
    pairs_eq = st.session_state.get("pairs_equity", [])
    if not mm_eq or not pairs_eq:
        st.info("Run both strategies to compare results.")
    else:
        mm_df = equity_to_df(mm_eq).rename(columns={"equity": "market_maker"})
        pairs_df = equity_to_df(pairs_eq).rename(columns={"equity": "pairs_trading"})
        merged = pd.merge(mm_df, pairs_df, on="timestamp", how="inner")
        st.line_chart(merged.set_index("timestamp"), height=250)

with tabs[4]:
    st.subheader("Portfolio VaR")
    st.markdown("Calculate portfolio Value-at-Risk using Multi-Asset Monte Carlo, Bootstrap, or GARCH.")

    var_method = st.selectbox("VaR Method", ["Multi-Asset Monte Carlo", "Bootstrap", "GARCH"])

    col_param1, col_param2, col_param3 = st.columns(3)
    with col_param1:
        portfolio_value = st.number_input("Portfolio Value ($)", min_value=1000.0, value=100000.0, step=1000.0)
        alpha = st.slider("Confidence Level (α)", 0.01, 0.20, 0.05, 0.01)
    with col_param2:
        horizon = st.number_input("Horizon (days)", min_value=1, value=1, step=1)
        simulations = st.number_input("Simulations", min_value=1000, value=10000, step=1000)
    with col_param3:
        data_length = st.number_input("Historical Data Length", min_value=50, value=252, step=10)

    data_input_method = st.radio(
        "Data Input Method",
        ["Generate Synthetic Multi-Asset Data", "Use Strategy Results", "Upload CSV"],
        horizontal=True,
    )

    returns_data = None
    returns_matrix = None
    num_assets = 3

    if data_input_method == "Generate Synthetic Multi-Asset Data":
        num_assets = st.number_input("Number of Assets", min_value=2, max_value=10, value=3, step=1)
        if st.button("Generate Synthetic Returns", key="gen_synthetic"):
            np.random.seed(42)
            mean_returns = np.random.uniform(-0.001, 0.001, num_assets)
            A = np.random.rand(num_assets, num_assets)
            corr_matrix = A @ A.T
            diag_sqrt = np.sqrt(np.diag(corr_matrix))
            corr_matrix = corr_matrix / diag_sqrt[:, None] / diag_sqrt[None, :]
            vols = np.random.uniform(0.01, 0.03, num_assets)
            cov_matrix = np.outer(vols, vols) * corr_matrix
            returns_matrix = np.random.multivariate_normal(mean_returns, cov_matrix, size=data_length)
            st.session_state["returns_matrix"] = returns_matrix
            st.session_state["returns_data"] = None
            st.success(f"Generated {data_length} periods of returns for {num_assets} assets")
            st.dataframe(pd.DataFrame(returns_matrix, columns=[f"Asset {i+1}" for i in range(num_assets)]).head(10))
        if "returns_matrix" in st.session_state:
            returns_matrix = st.session_state["returns_matrix"]
            num_assets = returns_matrix.shape[1]

    elif data_input_method == "Use Strategy Results":
        demo_choice = st.selectbox("Select Strategy", ["Market Maker", "Pairs Trading"])
        equity_history = st.session_state.get("mm_equity", []) if demo_choice == "Market Maker" else st.session_state.get("pairs_equity", [])
        if equity_history:
            values = [v for (_t, v) in equity_history]
            returns_data = np.array([values[i + 1] / values[i] - 1.0 for i in range(len(values) - 1)])
            st.session_state["returns_data"] = returns_data
            st.session_state["returns_matrix"] = None
            st.success(f"Loaded {len(returns_data)} returns from {demo_choice} results")
        else:
            st.warning("Run the strategy first to generate equity history.")

    elif data_input_method == "Upload CSV":
        uploaded_file = st.file_uploader("Upload Returns CSV", type=["csv"])
        if uploaded_file is not None:
            try:
                if uploaded_file.size > 10 * 1024 * 1024:
                    st.error("File too large. Maximum size is 10MB.")
                else:
                    df = pd.read_csv(uploaded_file)
                    if df.empty:
                        st.error("CSV file is empty.")
                    elif df.shape[0] < 2:
                        st.error("CSV must contain at least 2 rows.")
                    else:
                        numeric_cols = df.select_dtypes(include=[np.number]).columns
                        if len(numeric_cols) != df.shape[1]:
                            st.warning(f"Non-numeric columns detected. Using only numeric columns: {list(numeric_cols)}")
                            df = df[numeric_cols]
                        if df.shape[1] == 1:
                            returns_data = df.iloc[:, 0].values
                            returns_data = returns_data[np.isfinite(returns_data)]
                            if len(returns_data) < 2:
                                st.error("Insufficient valid data points after cleaning.")
                            else:
                                st.session_state["returns_data"] = returns_data
                                st.session_state["returns_matrix"] = None
                                st.success(f"Loaded {len(returns_data)} periods, 1 asset")
                        else:
                            returns_matrix = df.values
                            valid_mask = np.all(np.isfinite(returns_matrix), axis=1)
                            returns_matrix = returns_matrix[valid_mask]
                            if returns_matrix.shape[0] < 2:
                                st.error("Insufficient valid data points after cleaning.")
                            else:
                                num_assets = returns_matrix.shape[1]
                                st.session_state["returns_matrix"] = returns_matrix
                                st.session_state["returns_data"] = None
                                st.success(f"Loaded {returns_matrix.shape[0]} periods, {num_assets} assets")
            except Exception as e:
                st.error(f"Error loading CSV: {str(e)}")

        if "returns_matrix" in st.session_state and st.session_state["returns_matrix"] is not None:
            returns_matrix = st.session_state["returns_matrix"]
            num_assets = returns_matrix.shape[1] if returns_matrix.ndim == 2 else 1
        if "returns_data" in st.session_state and st.session_state["returns_data"] is not None:
            returns_data = st.session_state["returns_data"]

    if var_method == "Multi-Asset Monte Carlo":
        st.subheader("Multi-Asset Monte Carlo VaR")
        if returns_matrix is not None and returns_matrix.ndim == 2:
            st.markdown("Portfolio Weights (must sum to 1.0)")
            weight_cols = st.columns(num_assets)
            weights = []
            for i in range(num_assets):
                with weight_cols[i]:
                    w = st.number_input(f"Asset {i+1}", min_value=0.0, max_value=1.0, value=1.0 / num_assets, step=0.01, key=f"weight_{i}")
                    weights.append(w)
            weight_sum = sum(weights)
            if abs(weight_sum - 1.0) > 0.01:
                st.warning(f"Weights sum to {weight_sum:.3f}. Normalizing to 1.0.")
                weights = [w / weight_sum for w in weights]
            if st.button("Calculate VaR", key="calc_mc"):
                var_result = multi_asset_monte_carlo_var(
                    returns_matrix,
                    weights=weights,
                    alpha=alpha,
                    horizon=horizon,
                    simulations=simulations,
                    portfolio_value=portfolio_value,
                )
                st.success(f"Monte Carlo VaR (95%): ${var_result:,.2f}")
        else:
            st.warning("Provide multi-asset returns data for Monte Carlo VaR.")

    elif var_method == "Bootstrap":
        st.subheader("Bootstrap VaR")
        if returns_data is not None:
            if st.button("Calculate VaR", key="calc_bootstrap"):
                var_result = bootstrap_var(
                    returns_data,
                    alpha=alpha,
                    horizon=horizon,
                    simulations=simulations,
                    portfolio_value=portfolio_value,
                )
                st.success(f"Bootstrap VaR (95%): ${var_result:,.2f}")
                st.markdown("Return Statistics")
                st.write(f"Mean: {np.mean(returns_data):.5f}")
                st.write(f"Std Dev: {np.std(returns_data):.5f}")
                st.write(f"Min: {np.min(returns_data):.5f}")
                st.write(f"Max: {np.max(returns_data):.5f}")
        else:
            st.warning("Provide single-asset returns data for Bootstrap VaR.")

    elif var_method == "GARCH":
        st.subheader("GARCH VaR")
        if returns_data is not None:
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                omega = st.number_input("Omega", value=0.000001, format="%.8f")
                alpha_garch = st.number_input("Alpha", value=0.05, format="%.3f")
            with col_g2:
                beta_garch = st.number_input("Beta", value=0.94, format="%.3f")
            if st.button("Calculate VaR", key="calc_garch"):
                var_result = garch_var(
                    returns_data,
                    alpha=alpha,
                    horizon=horizon,
                    omega=omega,
                    alpha_param=alpha_garch,
                    beta_param=beta_garch,
                    portfolio_value=portfolio_value,
                )
                st.success(f"GARCH VaR (95%): ${var_result:,.2f}")
        else:
            st.warning("Provide single-asset returns data for GARCH VaR.")
