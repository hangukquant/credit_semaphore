import time
import asyncio
from credit_semaphore.async_credit_semaphore import AsyncCreditSemaphore


async def failure():
    await asyncio.sleep(3)
    raise Exception("i am a failure")

async def do_test():
    sem = AsyncCreditSemaphore(10)
    print("state 1", sem)
    try:
        await sem.transact(failure(), 4, 0)
    except Exception as err:
        print(err)
    print("state 2", sem)
    try:
        await sem.transact(failure(), 4, 0)
    except Exception as err:
        print(err)
    print("state 3", sem)
    try:
        await sem.transact(failure(), 4, 0)
    except Exception as err:
        print(err)



async def tasks_are_not_coroutines():
    async def say_hi(start):
        print("hi")
        print(f"hi said after {time.time() - start}")
        return

    start = time.time()
    loop = asyncio.get_event_loop()    
    task = loop.create_task(say_hi(start))
    await asyncio.sleep(3) #triggers iteration of the event loop and say_hi immediately gets called
    await task

    start = time.time()
    cor = say_hi(start)
    await asyncio.sleep(3) #created coroutine is not on the event loop and is only called after sleeping
    await cor

async def example():

    import random
    from datetime import datetime

    async def getTick(work, id):
        print(f"{datetime.now()}::getTick processing {id} takes {work} seconds")
        await asyncio.sleep(work)
        print(f"{datetime.now()}::getTick processed {id}")
        return True

    async def getOHLCV(work, id):
        print(f"{datetime.now()}::getOHLCV processing {id} takes {work} seconds")
        await asyncio.sleep(work)
        print(f"{datetime.now()}::getOHLCV processed {id}")
        return True

    async def getPrice(work, id):
        print(f"{datetime.now()}::getPrice processing {id} takes {work} seconds")
        await asyncio.sleep(work)
        print(f"{datetime.now()}::getPrice processed {id}")
        return True

    sem = AsyncCreditSemaphore(40)

    tick_req = lambda x: getTick(random.randint(1, 5), x)
    ohlcv_req = lambda x: getOHLCV(random.randint(1, 5), x)
    price_req = lambda x: getPrice(random.randint(1, 5), x)

    transactions = [
        sem.transact(coroutine=tick_req(1), credits=20, refund_time=10, transaction_id=1, verbose=True),
        sem.transact(coroutine=ohlcv_req(2), credits=30, refund_time=10, transaction_id=2, verbose=True),
        sem.transact(coroutine=ohlcv_req(3), credits=30, refund_time=10, transaction_id=3, verbose=True),
        sem.transact(coroutine=price_req(4), credits=5, refund_time=10, transaction_id=4, verbose=True),
        sem.transact(coroutine=tick_req(5), credits=20, refund_time=10, transaction_id=5, verbose=True),
        sem.transact(coroutine=tick_req(6), credits=20, refund_time=10, transaction_id=6, verbose=True),
    ]

    results = await asyncio.gather(*transactions)
    


if __name__ == "__main__":
    asyncio.run(example())
    asyncio.run(do_test())
    asyncio.run(tasks_are_not_coroutines())  