import random
import time

def stream_ticks():
    price = 3360.0
    while True:
        price += random.uniform(-0.8, 0.8)
        yield {
            "price": round(price, 2),
            "qty": random.randint(100, 1500),
            "side": random.choice(["buy", "sell"]),
            "timestamp": time.time()
        }
        time.sleep(0.2)
