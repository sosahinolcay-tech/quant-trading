"""Simple CLI to run demo simulation"""
import click
from qt.engine.engine import SimulationEngine
from qt.strategies.market_maker import SimpleMarketMaker


@click.command()
@click.option("--demo", is_flag=True, help="Run demo backtest")
def main(demo: bool):
    if demo:
        engine = SimulationEngine()
        strat = SimpleMarketMaker(symbol="TEST")
        engine.register_strategy(strat)
        engine.run_demo()
        print("Demo complete")


if __name__ == "__main__":
    main()
