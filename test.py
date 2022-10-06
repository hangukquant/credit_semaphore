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


if __name__ == "__main__":
    #async_credit_sem = AsyncCreditSemaphore(10)
    asyncio.run(do_test())
    asyncio.run(tasks_are_not_coroutines())  