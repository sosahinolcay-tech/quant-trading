import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import subprocess
import sys
import os
import csv

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
    """Load equity curve from CSV"""
    if os.path.exists(csv_path):
        data = []
        with open(csv_path, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                if len(row) >= 2:
                    data.append((float(row[0]), float(row[1])))
        return data
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

# Footer
st.markdown('---')
st.markdown('Built with ❤️ using Streamlit | [GitHub](https://github.com/sosahinolcay-tech/quant-trading)')
