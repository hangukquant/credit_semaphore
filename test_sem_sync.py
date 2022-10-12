import time
import asyncio
import random
import functools

from datetime import datetime
from credit_semaphore.semutils import consume_credits
from credit_semaphore.sync_credit_semaphore import SyncCreditSemaphore

def getTick(work, id):
    print(f"{datetime.now()}::getTick processing {id} takes {work} seconds")
    time.sleep(work)
    print(f"{datetime.now()}::getTick processed {id}")
    return True

def getOHLCV(work, id):
    print(f"{datetime.now()}::getOHLCV processing {id} takes {work} seconds")
    time.sleep(work)
    print(f"{datetime.now()}::getOHLCV processed {id}")
    return True

def getPrice(work, id):
    print(f"{datetime.now()}::getPrice processing {id} takes {work} seconds")
    time.sleep(work)
    print(f"{datetime.now()}::getPrice processed {id}")
    return True

async def example():
    sem = SyncCreditSemaphore(40)
    
    tick_req = lambda x: getTick(random.randint(1, 5), x)
    ohlcv_req = lambda x: getOHLCV(random.randint(1, 5), x)
    price_req = lambda x: getPrice(random.randint(1, 5), x)

    loop = asyncio.get_event_loop()
    tasks = [
        loop.run_in_executor(
            None,
            functools.partial(sem.transact, lambda: tick_req(1), credits=20, refund_time=10, transaction_id=1, verbose=True)
        ),
        loop.run_in_executor(
            None,
            functools.partial(sem.transact, lambda:ohlcv_req(2), credits=30, refund_time=10, transaction_id=2, verbose=True)
        ),
        loop.run_in_executor(
            None,
            functools.partial(sem.transact, lambda:ohlcv_req(3), credits=30, refund_time=10, transaction_id=3, verbose=True)
        ),
        loop.run_in_executor(
            None,
            functools.partial(sem.transact, lambda:price_req(4), credits=5, refund_time=10, transaction_id=4, verbose=True)
        ),
        loop.run_in_executor(
            None,
            functools.partial(sem.transact, lambda: tick_req(5), credits=20, refund_time=10, transaction_id=5, verbose=True)
        ),
        loop.run_in_executor(
            None,
            functools.partial(sem.transact, lambda: tick_req(6), credits=20, refund_time=10, transaction_id=6, verbose=True)
        ),
    ]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(example())