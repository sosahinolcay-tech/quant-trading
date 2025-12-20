import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import subprocess
import sys
import os
import csv
import numpy as np
from qt.analytics.risk import stress_test_equity, monte_carlo_horizon_var, compute_var, compute_cvar
from qt.analytics.risk_ext import multi_asset_monte_carlo_var, bootstrap_var, garch_var

st.set_page_config(page_title="Quant Trading Dashboard", layout="wide")
st.title('📈 Quant Trading Framework Dashboard')

# Sidebar for configuration
st.sidebar.header('⚙️ Configuration')
data_source = st.sidebar.selectbox(
    'Data Source',
    ['synthetic', 'yahoo'],
    help='Choose data source for backtesting'
)

# Strategy parameters
st.sidebar.header('🎯 Strategy Parameters')

# Market Maker params
st.sidebar.subheader('Market Maker')
mm_risk_aversion = st.sidebar.slider('Risk Aversion', 0.01, 1.0, 0.1, 0.01)
mm_max_inventory = st.sidebar.slider('Max Inventory', 10, 1000, 100)

# Pairs params
st.sidebar.subheader('Pairs Trading')
pairs_window = st.sidebar.slider('Rolling Window', 10, 100, 50)
pairs_entry_z = st.sidebar.slider('Entry Z-Score', 1.0, 3.0, 1.5, 0.1)
pairs_exit_z = st.sidebar.slider('Exit Z-Score', 0.1, 1.0, 0.5, 0.1)

def load_equity_curve(csv_path):
    """Load equity curve from CSV with validation.
    
    Args:
        csv_path: Path to CSV file (relative or absolute)
    
    Returns:
        List of (timestamp, equity) tuples or None if file not found/invalid
    """
    # Validate and sanitize path
    if not csv_path or not isinstance(csv_path, str):
        return None
    
    # Handle both absolute and relative paths
    if not os.path.isabs(csv_path):
        # If relative, make it relative to project root
        base_dir = os.path.dirname(__file__) + '/../'
        csv_path = os.path.join(base_dir, csv_path)
    
    # Normalize path to prevent directory traversal
    csv_path = os.path.normpath(csv_path)
    
    # Validate path is within project directory
    project_root = os.path.normpath(os.path.dirname(__file__) + '/../')
    if not csv_path.startswith(project_root):
        return None  # Path traversal attempt
    
    if os.path.exists(csv_path) and os.path.isfile(csv_path):
        try:
            data = []
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                for row in reader:
                    if len(row) >= 2:
                        try:
                            timestamp = float(row[0])
                            equity = float(row[1])
                            # Validate values are finite
                            if np.isfinite(timestamp) and np.isfinite(equity) and equity > 0:
                                data.append((timestamp, equity))
                        except (ValueError, TypeError):
                            continue  # Skip invalid rows
            return data if data else None
        except (IOError, OSError, csv.Error):
            return None
    return None

def plot_equity_curve(equity_data, title):
    """Plot equity curve"""
    if not equity_data:
        return None

    timestamps, values = zip(*equity_data)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(timestamps, values)
    ax.set_title(title)
    ax.set_xlabel('Time')
    ax.set_ylabel('Equity')
    ax.grid(True, alpha=0.3)
    return fig

# Main content
col1, col2 = st.columns(2)

with col1:
    st.header('🤖 Market Maker Demo')
    if st.button('Run Market Maker Demo', key='mm_demo'):
        with st.spinner('Running market maker simulation...'):
            # Update parameters in demo script or pass via env
            env = os.environ.copy()
            env['MM_RISK_AVERSION'] = str(mm_risk_aversion)
            env['MM_MAX_INVENTORY'] = str(mm_max_inventory)
            env['DATA_SOURCE'] = data_source

            result = subprocess.run(
                [sys.executable, 'tools/run_demo.py'],
                capture_output=True, text=True,
                cwd=os.path.dirname(__file__) + '/../',
                env=env
            )

            if result.returncode == 0:
                st.success('Market maker demo completed!')
                st.text(result.stdout[-500:])  # Last 500 chars

                # Load and display metrics
                csv_path = 'notebooks/summary_metrics_demo.csv'
                if os.path.exists(csv_path):
                    df = pd.read_csv(csv_path)
                    st.dataframe(df, use_container_width=True)

                # Load and plot equity curve
                equity_path = 'notebooks/equity_demo.csv'
                equity_data = load_equity_curve(equity_path)
                if equity_data:
                    fig = plot_equity_curve(equity_data, 'Market Maker Equity Curve')
                    st.pyplot(fig)
                    # Risk metrics
                    values = [v for (_t, v) in equity_data]
                    if len(values) > 1:
                        rets = [values[i+1] / values[i] - 1.0 for i in range(len(values)-1)]
                        var_95 = compute_var(rets, alpha=0.05, method='historical')
                        cvar_95 = compute_cvar(rets, alpha=0.05, method='historical')
                        mc_var_5d = monte_carlo_horizon_var(rets, alpha=0.05, horizon=5, simulations=2000)
                        st.metric('VaR (95%)', f"{var_95:.4f}")
                        st.metric('CVaR (95%)', f"{cvar_95:.4f}")
                        st.metric('MC VaR 5d (95%)', f"{mc_var_5d:.4f}")
                        if st.button('Apply -30% Shock', key='mm_shock'):
                            stressed = stress_test_equity(values, shock_pct=-0.3)
                            fig2 = plot_equity_curve(list(enumerate(stressed['stressed_equity'])), 'Stressed Equity')
                            st.pyplot(fig2)
            else:
                st.error('Demo failed')
                st.text(result.stderr)

with col2:
    st.header('⚖️ Pairs Trading Demo')
    if st.button('Run Pairs Demo', key='pairs_demo'):
        with st.spinner('Running pairs trading simulation...'):
            env = os.environ.copy()
            env['PAIRS_WINDOW'] = str(pairs_window)
            env['PAIRS_ENTRY_Z'] = str(pairs_entry_z)
            env['PAIRS_EXIT_Z'] = str(pairs_exit_z)
            env['DATA_SOURCE'] = data_source

            result = subprocess.run(
                [sys.executable, 'tools/demo_pairs.py'],
                capture_output=True, text=True,
                cwd=os.path.dirname(__file__) + '/../',
                env=env
            )

            if result.returncode == 0:
                st.success('Pairs trading demo completed!')
                st.text(result.stdout[-500:])

                # Load and display metrics
                csv_path = 'notebooks/summary_metrics_pairs_demo.csv'
                if os.path.exists(csv_path):
                    df = pd.read_csv(csv_path)
                    st.dataframe(df, use_container_width=True)

                # Load and plot equity curve
                equity_path = 'notebooks/equity_pairs_demo.csv'
                equity_data = load_equity_curve(equity_path)
                if equity_data:
                    fig = plot_equity_curve(equity_data, 'Pairs Trading Equity Curve')
                    st.pyplot(fig)
                    # Risk metrics
                    values = [v for (_t, v) in equity_data]
                    if len(values) > 1:
                        rets = [values[i+1] / values[i] - 1.0 for i in range(len(values)-1)]
                        var_95 = compute_var(rets, alpha=0.05, method='historical')
                        cvar_95 = compute_cvar(rets, alpha=0.05, method='historical')
                        mc_var_5d = monte_carlo_horizon_var(rets, alpha=0.05, horizon=5, simulations=2000)
                        st.metric('VaR (95%)', f"{var_95:.4f}")
                        st.metric('CVaR (95%)', f"{cvar_95:.4f}")
                        st.metric('MC VaR 5d (95%)', f"{mc_var_5d:.4f}")
                        if st.button('Apply -30% Shock', key='pairs_shock'):
                            stressed = stress_test_equity(values, shock_pct=-0.3)
                            fig2 = plot_equity_curve(list(enumerate(stressed['stressed_equity'])), 'Stressed Equity')
                            st.pyplot(fig2)
            else:
                st.error('Demo failed')
                st.text(result.stderr)

st.header('🔄 Walk-Forward Analysis')
if st.button('Run Walk-Forward Analysis'):
    with st.spinner('Running walk-forward analysis...'):
        result = subprocess.run(
            [sys.executable, 'tools/walk_forward.py'],
            capture_output=True, text=True,
            cwd=os.path.dirname(__file__) + '/../',
            env={**os.environ, 'PYTHONPATH': os.path.dirname(__file__) + '/../'}
        )

        if result.returncode == 0:
            st.success('Walk-forward analysis completed!')
            st.text(result.stdout[-1000:])  # Last 1000 chars
        else:
            st.error('Walk-forward failed')
            st.text(result.stderr)

st.header('📊 Portfolio VaR Calculator (Week 5)')
st.markdown('Calculate portfolio Value-at-Risk using multiple methods: Multi-Asset Monte Carlo, Bootstrap, or GARCH.')

# VaR Method Selection
var_method = st.selectbox(
    'VaR Method',
    ['Multi-Asset Monte Carlo', 'Bootstrap', 'GARCH'],
    help='Select the VaR calculation method'
)

# Common parameters
col_param1, col_param2, col_param3 = st.columns(3)
with col_param1:
    portfolio_value = st.number_input('Portfolio Value ($)', min_value=1000.0, value=100000.0, step=1000.0)
    alpha = st.slider('Confidence Level (α)', 0.01, 0.20, 0.05, 0.01, help='Tail probability (0.05 = 95% VaR)')
with col_param2:
    horizon = st.number_input('Horizon (days)', min_value=1, value=1, step=1)
    simulations = st.number_input('Simulations', min_value=1000, value=10000, step=1000)
with col_param3:
    data_length = st.number_input('Historical Data Length', min_value=50, value=252, step=10, 
                                   help='Number of historical periods to generate/use')

# Data source selection
data_input_method = st.radio(
    'Data Input Method',
    ['Generate Synthetic Multi-Asset Data', 'Use Equity Curve from Demo', 'Upload CSV'],
    horizontal=True
)

returns_data = None
returns_matrix = None
num_assets = 3  # Default for synthetic

if data_input_method == 'Generate Synthetic Multi-Asset Data':
    num_assets = st.number_input('Number of Assets', min_value=2, max_value=10, value=3, step=1)
    if st.button('Generate Synthetic Returns', key='gen_synthetic'):
        np.random.seed(42)
        # Generate correlated returns using multivariate normal
        mean_returns = np.random.uniform(-0.001, 0.001, num_assets)
        # Create a positive definite correlation matrix
        # Generate random matrix and make it positive semi-definite
        A = np.random.rand(num_assets, num_assets)
        corr_matrix = A @ A.T
        # Normalize to have 1s on diagonal (proper correlation matrix)
        diag_sqrt = np.sqrt(np.diag(corr_matrix))
        corr_matrix = corr_matrix / diag_sqrt[:, None] / diag_sqrt[None, :]
        vols = np.random.uniform(0.01, 0.03, num_assets)
        cov_matrix = np.outer(vols, vols) * corr_matrix
        
        returns_matrix = np.random.multivariate_normal(mean_returns, cov_matrix, size=data_length)
        st.session_state['returns_matrix'] = returns_matrix
        st.session_state['returns_data'] = None  # Clear single-asset data
        st.success(f'Generated {data_length} periods of returns for {num_assets} assets')
        st.dataframe(pd.DataFrame(returns_matrix, columns=[f'Asset {i+1}' for i in range(num_assets)]).head(10))
    
    if 'returns_matrix' in st.session_state:
        returns_matrix = st.session_state['returns_matrix']
        num_assets = returns_matrix.shape[1]

elif data_input_method == 'Use Equity Curve from Demo':
    demo_choice = st.selectbox('Select Demo', ['Market Maker', 'Pairs Trading'])
    if st.button('Load Equity Curve', key='load_equity'):
        # Use relative path - load_equity_curve will handle path resolution
        if demo_choice == 'Market Maker':
            equity_path = 'notebooks/equity_demo.csv'
        else:
            equity_path = 'notebooks/equity_pairs_demo.csv'
        
        equity_data = load_equity_curve(equity_path)
        if equity_data:
            values = [v for (_t, v) in equity_data]
            if len(values) > 1:
                returns_data = np.array([values[i+1] / values[i] - 1.0 for i in range(len(values)-1)])
                st.session_state['returns_data'] = returns_data
                st.session_state['returns_matrix'] = None  # Clear multi-asset data
                st.success(f'Loaded {len(returns_data)} returns from {demo_choice} demo')
            else:
                st.error('Insufficient data in equity curve')
        else:
            st.error(f'Equity curve file not found: {equity_path}')
    
    if 'returns_data' in st.session_state:
        returns_data = st.session_state['returns_data']

elif data_input_method == 'Upload CSV':
    uploaded_file = st.file_uploader('Upload Returns CSV', type=['csv'], 
                                      help='CSV file with returns. Each column = one asset, each row = one period')
    if uploaded_file is not None:
        try:
            # Validate file size (limit to 10MB)
            if uploaded_file.size > 10 * 1024 * 1024:
                st.error('File too large. Maximum size is 10MB.')
            else:
                df = pd.read_csv(uploaded_file)
                
                # Validate DataFrame structure
                if df.empty:
                    st.error('CSV file is empty.')
                elif df.shape[0] < 2:
                    st.error('CSV file must contain at least 2 rows (periods).')
                elif df.shape[1] == 0:
                    st.error('CSV file has no columns.')
                else:
                    # Validate numeric data
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    if len(numeric_cols) != df.shape[1]:
                        st.warning(f'Non-numeric columns detected. Using only numeric columns: {list(numeric_cols)}')
                        df = df[numeric_cols]
                    
                    if df.empty:
                        st.error('No numeric data found in CSV file.')
                    else:
                        # Handle both 1D and 2D cases
                        if df.shape[1] == 1:
                            # Single column - treat as single asset returns
                            returns_data = df.iloc[:, 0].values
                            # Validate returns are finite
                            if not np.all(np.isfinite(returns_data)):
                                st.warning('CSV contains non-finite values (NaN/Inf). These will be removed.')
                                returns_data = returns_data[np.isfinite(returns_data)]
                            if len(returns_data) < 2:
                                st.error('Insufficient valid data points after cleaning.')
                            else:
                                returns_matrix = None
                                num_assets = 1
                                st.session_state['returns_data'] = returns_data
                                st.session_state['returns_matrix'] = None
                                st.success(f'Loaded {len(returns_data)} periods, {num_assets} asset(s)')
                                st.dataframe(df.head(10))
                        else:
                            # Multiple columns - treat as multi-asset returns
                            returns_matrix = df.values
                            # Validate returns are finite
                            if not np.all(np.isfinite(returns_matrix)):
                                st.warning('CSV contains non-finite values (NaN/Inf). Rows with invalid data will be removed.')
                                valid_mask = np.all(np.isfinite(returns_matrix), axis=1)
                                returns_matrix = returns_matrix[valid_mask]
                            if returns_matrix.shape[0] < 2:
                                st.error('Insufficient valid data points after cleaning.')
                            else:
                                num_assets = returns_matrix.shape[1]
                                returns_data = None
                                st.session_state['returns_matrix'] = returns_matrix
                                st.session_state['returns_data'] = None
                                st.success(f'Loaded {returns_matrix.shape[0]} periods, {num_assets} asset(s)')
                                st.dataframe(df.head(10))
        except pd.errors.EmptyDataError:
            st.error('CSV file is empty or invalid.')
        except pd.errors.ParserError as e:
            st.error(f'Error parsing CSV file: {str(e)}')
        except Exception as e:
            st.error(f'Error loading CSV: {str(e)}')
    
    # Load from session state if available
    if 'returns_matrix' in st.session_state and st.session_state['returns_matrix'] is not None:
        returns_matrix = st.session_state['returns_matrix']
        num_assets = returns_matrix.shape[1] if returns_matrix.ndim == 2 else 1
    if 'returns_data' in st.session_state and st.session_state['returns_data'] is not None:
        returns_data = st.session_state['returns_data']

# Method-specific parameters and calculation
if var_method == 'Multi-Asset Monte Carlo':
    st.subheader('Multi-Asset Monte Carlo VaR')
    st.markdown('Calculates VaR for a portfolio with multiple assets using multivariate normal Monte Carlo simulation.')
    
    if returns_matrix is not None and returns_matrix.ndim == 2:
        # Portfolio weights input
        st.markdown('**Portfolio Weights** (must sum to 1.0)')
        weight_cols = st.columns(num_assets)
        weights = []
        for i in range(num_assets):
            with weight_cols[i]:
                w = st.number_input(f'Asset {i+1}', min_value=0.0, max_value=1.0, value=1.0/num_assets, 
                                    step=0.01, key=f'weight_{i}')
                weights.append(w)
        
        weight_sum = sum(weights)
        if abs(weight_sum - 1.0) > 0.01:
            st.warning(f'⚠️ Weights sum to {weight_sum:.3f}. Normalizing to sum to 1.0.')
            weights = [w / weight_sum for w in weights]
        else:
            st.success(f'✓ Weights sum to {weight_sum:.3f}')
        
        if st.button('Calculate Multi-Asset MC VaR', key='calc_mc_var'):
            try:
                with st.spinner('Calculating VaR...'):
                    var_result = multi_asset_monte_carlo_var(
                        returns_matrix=returns_matrix,
                        weights=np.array(weights),
                        portfolio_value=portfolio_value,
                        alpha=alpha,
                        horizon=horizon,
                        simulations=simulations
                    )
                    
                    st.success('VaR calculation completed!')
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric('Portfolio VaR ($)', f"${var_result:,.2f}")
                    with col2:
                        st.metric('Portfolio VaR (%)', f"{(var_result/portfolio_value)*100:.2f}%")
                    with col3:
                        confidence_pct = (1 - alpha) * 100
                        st.metric(f'Confidence Level', f"{confidence_pct:.0f}%")
                    
                    # Display portfolio composition
                    st.subheader('Portfolio Composition')
                    comp_df = pd.DataFrame({
                        'Asset': [f'Asset {i+1}' for i in range(num_assets)],
                        'Weight': [f'{w*100:.2f}%' for w in weights],
                        'Value ($)': [f'${w*portfolio_value:,.2f}' for w in weights]
                    })
                    st.dataframe(comp_df, use_container_width=True)
            except Exception as e:
                st.error(f'Error calculating VaR: {str(e)}')
    else:
        st.info('Please generate or upload multi-asset returns data (2D matrix) for Multi-Asset Monte Carlo VaR.')

elif var_method == 'Bootstrap':
    st.subheader('Bootstrap VaR')
    st.markdown('Estimates VaR by bootstrap resampling historical returns (non-parametric method).')
    
    # For bootstrap, we can use either single asset or portfolio returns
    # If multi-asset data is available, allow user to compute portfolio returns first
    if returns_matrix is not None and returns_matrix.ndim == 2:
        st.info('💡 Multi-asset data detected. Bootstrap will use the first asset only, or you can switch to "Use Equity Curve from Demo" for portfolio returns.')
        # Optionally compute portfolio returns if weights are provided
        # For now, just use first asset
        if returns_data is None:
            returns_data = returns_matrix[:, 0]  # Use first asset
    
    if returns_data is not None:
        if st.button('Calculate Bootstrap VaR', key='calc_bootstrap_var'):
            try:
                with st.spinner('Calculating VaR...'):
                    var_result = bootstrap_var(
                        returns=returns_data,
                        alpha=alpha,
                        horizon=horizon,
                        simulations=simulations
                    )
                    
                    var_result_dollar = var_result * portfolio_value
                    
                    st.success('VaR calculation completed!')
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric('Portfolio VaR ($)', f"${var_result_dollar:,.2f}")
                    with col2:
                        st.metric('Portfolio VaR (%)', f"{var_result*100:.2f}%")
                    with col3:
                        confidence_pct = (1 - alpha) * 100
                        st.metric(f'Confidence Level', f"{confidence_pct:.0f}%")
                    
                    # Show return statistics
                    st.subheader('Return Statistics')
                    stats_df = pd.DataFrame({
                        'Statistic': ['Mean', 'Std Dev', 'Min', 'Max', 'Skewness', 'Kurtosis'],
                        'Value': [
                            f"{np.mean(returns_data):.6f}",
                            f"{np.std(returns_data):.6f}",
                            f"{np.min(returns_data):.6f}",
                            f"{np.max(returns_data):.6f}",
                            f"{float(pd.Series(returns_data).skew()):.4f}",
                            f"{float(pd.Series(returns_data).kurtosis()):.4f}"
                        ]
                    })
                    st.dataframe(stats_df, use_container_width=True)
            except Exception as e:
                st.error(f'Error calculating VaR: {str(e)}')
    else:
        st.info('Please load or generate returns data for Bootstrap VaR.')

elif var_method == 'GARCH':
    st.subheader('GARCH VaR')
    st.markdown('Estimates VaR using a GARCH(1,1)-like volatility model.')
    
    # GARCH parameters
    st.markdown('**GARCH Parameters**')
    garch_col1, garch_col2, garch_col3 = st.columns(3)
    with garch_col1:
        omega = st.number_input('Omega (ω)', min_value=1e-8, value=1e-6, format='%.2e', 
                                help='Long-term variance')
    with garch_col2:
        alpha_g = st.slider('Alpha (α)', 0.0, 0.5, 0.05, 0.01, 
                           help='Sensitivity to recent shocks')
    with garch_col3:
        beta = st.slider('Beta (β)', 0.0, 0.99, 0.9, 0.01, 
                        help='Persistence of volatility')
    
    # For GARCH, we can use either single asset or portfolio returns
    # If multi-asset data is available, allow user to compute portfolio returns first
    if returns_matrix is not None and returns_matrix.ndim == 2:
        st.info('💡 Multi-asset data detected. GARCH will use the first asset only, or you can switch to "Use Equity Curve from Demo" for portfolio returns.')
        # Optionally compute portfolio returns if weights are provided
        # For now, just use first asset
        if returns_data is None:
            returns_data = returns_matrix[:, 0]  # Use first asset
    
    if returns_data is not None:
        if st.button('Calculate GARCH VaR', key='calc_garch_var'):
            try:
                with st.spinner('Calculating VaR...'):
                    var_result = garch_var(
                        returns=returns_data,
                        alpha=alpha,
                        horizon=horizon,
                        simulations=simulations,
                        omega=omega,
                        alpha_g=alpha_g,
                        beta=beta
                    )
                    
                    var_result_dollar = var_result * portfolio_value
                    
                    st.success('VaR calculation completed!')
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric('Portfolio VaR ($)', f"${var_result_dollar:,.2f}")
                    with col2:
                        st.metric('Portfolio VaR (%)', f"{var_result*100:.2f}%")
                    with col3:
                        confidence_pct = (1 - alpha) * 100
                        st.metric(f'Confidence Level', f"{confidence_pct:.0f}%")
                    
                    # Show GARCH model info
                    st.subheader('GARCH Model Information')
                    model_info = pd.DataFrame({
                        'Parameter': ['Omega (ω)', 'Alpha (α)', 'Beta (β)', 'Persistence (α+β)'],
                        'Value': [
                            f"{omega:.2e}",
                            f"{alpha_g:.4f}",
                            f"{beta:.4f}",
                            f"{alpha_g + beta:.4f}"
                        ],
                        'Description': [
                            'Long-term variance level',
                            'Sensitivity to recent shocks',
                            'Volatility persistence',
                            'Should be < 1.0 for stationarity'
                        ]
                    })
                    st.dataframe(model_info, use_container_width=True)
                    if alpha_g + beta >= 1.0:
                        st.warning('⚠️ α + β ≥ 1.0: Model may be non-stationary!')
            except Exception as e:
                st.error(f'Error calculating VaR: {str(e)}')
    else:
        st.info('Please load or generate returns data for GARCH VaR.')

# Footer
st.markdown('---')
st.markdown('Built using Streamlit | [GitHub](https://github.com/sosahinolcay-tech/quant-trading)')
