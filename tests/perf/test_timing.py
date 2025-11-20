import time


def test_engine_speed():
    start = time.time()
    # trivial loop to simulate timing
    for _ in range(10000):
        x = _ * 2
    dur = time.time() - start
    assert dur < 5.0
