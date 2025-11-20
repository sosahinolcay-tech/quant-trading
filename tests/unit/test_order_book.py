from qt.engine.order_book import OrderBook


def test_add_limit_order_and_fill():
    ob = OrderBook()
    ob.update_from_snapshot([(100.0, 10)], [(101.0, 12)])
    order_id = ob.add_limit_order('BUY', price=100.0, qty=5)
    fills = ob.process_trade(price=100.0, size=5)
    assert len(fills) == 1
    assert fills[0]['price'] == 100.0
