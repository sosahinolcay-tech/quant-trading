from qt.engine.execution import ExecutionModel
from qt.engine.order_book import OrderBook
from qt.engine.event import OrderEvent, FillEvent
from qt.risk.accounting import Account


def test_execution_model_slippage_and_fee():
    ob = OrderBook()
    # seed liquidity at price 100
    ob.update_from_snapshot([(99.0, 10)], [(101.0, 10)])
    # add some resting liquidity at 100 on the ask side to simulate depth
    ob.asks[100.0].append({"order_id": "rest1", "price": 100.0, "quantity": 100.0, "side": "SELL"})
    em = ExecutionModel(fee=0.01, slippage_coeff=0.1)
    # market buy order for qty 10 at price 100
    order = OrderEvent(
        order_id="o1", timestamp=0.0, symbol="TEST", side="BUY", price=100.0, quantity=10.0, order_type="MARKET"
    )
    fill = em.simulate_fill(order, order_book=ob)
    # slippage = 0.1 * (10/100) * 100 = 1 -> executed price ~101
    assert abs(fill.price - 101.0) < 1e-6
    # fee = 0.01 * (10 * 101) = 10.1
    assert abs(fill.fee - 10.1) < 1e-6


def test_account_fee_application():
    acct = Account(initial_cash=1000.0, fee=0.01)
    # Fill without explicit fee should use account-level fee
    fill = FillEvent(order_id="t1", timestamp=0.0, symbol="TEST", side="BUY", price=10.0, quantity=5.0, fee=0.0)
    acct.on_fill(fill)
    # positions updated
    assert acct.positions.get("TEST") == 5.0
    # cash = 1000 - 50 - (0.01 * 50) = 949.5
    assert abs(acct.cash - 949.5) < 1e-6
