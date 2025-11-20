import numpy as np
from qt.strategies.pairs import PairsStrategy
from qt.engine.engine import SimulationEngine


def walk_forward(run_windows, window_size=100):
    results = []
    for start in range(0, run_windows * window_size, window_size):
        eng = SimulationEngine()
        ps = PairsStrategy('X', 'Y', window=window_size)
        eng.register_strategy(ps)
        eng.run_demo()
        results.append(eng.order_book.last_price)
    return results
