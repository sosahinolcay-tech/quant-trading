import streamlit as st
import pandas as pd
import subprocess
import sys
import os
import csv

st.title('Quant Trading Dashboard')

st.header('Market Maker Demo')
if st.button('Run Market Maker Demo'):
    st.write('Running market maker demo...')
    result = subprocess.run([sys.executable, 'tools/demo_market_maker.py'], capture_output=True, text=True, cwd=os.path.dirname(__file__) + '/../')
    st.text(result.stdout)
    if result.stderr:
        st.error(result.stderr)
    # Load and display results
    csv_path = 'notebooks/summary_metrics_demo.csv'
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        st.dataframe(df)

st.header('Pairs Trading Demo')
if st.button('Run Pairs Demo'):
    st.write('Running pairs demo...')
    result = subprocess.run([sys.executable, 'tools/demo_pairs.py'], capture_output=True, text=True, cwd=os.path.dirname(__file__) + '/../')
    st.text(result.stdout)
    if result.stderr:
        st.error(result.stderr)
    # Load and display results
    csv_path = 'notebooks/summary_metrics_pairs_demo.csv'
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        st.dataframe(df)

st.header('Walk-Forward Analysis')
if st.button('Run Walk-Forward'):
    st.write('Running walk-forward analysis...')
    result = subprocess.run([sys.executable, 'tools/walk_forward.py'], capture_output=True, text=True, cwd=os.path.dirname(__file__) + '/../', env={**os.environ, 'PYTHONPATH': os.path.dirname(__file__) + '/../'})
    st.text(result.stdout)
    if result.stderr:
        st.error(result.stderr)
