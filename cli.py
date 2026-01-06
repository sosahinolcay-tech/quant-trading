"""Command-line interface for quant-trading framework"""
import click
from qt.engine.engine import SimulationEngine
from qt.strategies.market_maker import AvellanedaMarketMaker
from qt.strategies.pairs import PairsStrategy


@click.group()
def cli():
    """Quant Trading Framework CLI"""
    pass


@cli.command()
@click.option("--strategy", type=click.Choice(["market-maker", "pairs"]), default="market-maker", help="Strategy to run")
@click.option("--symbol", default="X", help="Symbol for market maker")
@click.option("--symbol-x", default="X", help="Symbol X for pairs")
@click.option("--symbol-y", default="Y", help="Symbol Y for pairs")
def demo(strategy, symbol, symbol_x, symbol_y):
    """Run demo backtest"""
    engine = SimulationEngine()

    if strategy == "market-maker":
        strat = AvellanedaMarketMaker(symbol=symbol)
        click.echo(f"Running market maker demo for {symbol}")
    else:
        strat = PairsStrategy(symbol_x=symbol_x, symbol_y=symbol_y)
        click.echo(f"Running pairs trading demo for {symbol_x}/{symbol_y}")

    engine.register_strategy(strat)
    engine.run_demo()

    # Show summary
    if hasattr(engine, 'trade_log') and engine.trade_log:
        click.echo(f"Trades: {len(engine.trade_log)}")
        click.echo(f"Turnover: {engine.turnover:.2f}")

    click.echo("Demo complete")


if __name__ == "__main__":
    cli()
