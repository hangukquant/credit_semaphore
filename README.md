# credit_semaphore
Asynchronous Semaphore Based on Credits for Efficient Credit-Based API Throttling
========

This library provides an asynchronous semaphore that generalizes the asyncio semaphore to handle rate limiting using a credit based system. A common use case is in API throttling, such as APIs that allow access limits up to '1000 requests / min' or '200 cpu credits / sec' and so on.

Usage
-----
A simple interface is provided for the credit semaphore.

```python
async def transact(self, coroutine, credits, refund_time, transaction_id=None, verbose=False):
    ...
```
The credit semaphore has a `transact` asynchronous function that takes in 3 key parameters

- `coroutine`: the coroutine to run, for instance `asyncio.sleep(1)`.
- `credits`: the number of credits (float or integer) the coroutine costs.
- `refund_time`: the time in seconds it takes for the credits to be returned to the semaphore.
- `transaction_id` (optional): this is an identifier for the transaction, and can be used with `verbose=True` for printing out when a particular transaction acquires and releases the semaphore.
- `verbose` (optional): prints to terminal the transaction status when acquiring and releasing the semaphore.

Installing
----------

From pip (https://pypi.org/project/credit-semaphore/):

```sh
pip install credit_semaphore
```

Example & Behavior
----
Suppose we have a financial API endpoint that has rate limits as such:
| Period     | Credits Awarded / app |
|------------|-----------------------|
| 10 seconds | 40                  |

The API gives us 40 credits to use every 10 seconds (capped at 40 credits max).
Different endpoints can have variable credit costs, depending on the server load. 

Suppose we have the following endpoints and their respective costs:
| Endpoint   | Cost (credits / req)  |
|------------|-----------------------|
| getTick    | 20                    |
| getOHLCV   | 30                    |
| getPrice   | 5                     |
| ...        | ...                   |

Our function calls are as simple as doing 

`semaphore.transact(getTick(), credits=x, refund_time=y)`

and awaiting this statement would give us the same result as `await getTick()`, except with the credit accounting.

#### Opportunistic on Exit
Suppose a completed transaction exits a semaphore with 2 waiting transactions, `txn A` arrival < `txn B`. If the semaphore has not enough credits to execute `txn A`, it can first run `txn B`. This helps to maximise throughput.

#### Fair on Entry
If a new transaction is submitted to the semaphore with enough credits to execute but with existing waiter transactions, the new transaction queues behind the current waiters. This helps with fairness of transaction priorities.

###### Note that the opportunistic exit and fair entry means that if a big transaction is sitting behind small transactions which are constantly being submitted to the semaphore at a fast rate, the big transaction will not get a chance to run.

#### FIFO Behavior
If there are multiple waiters in the semaphore, and multiple tasks have enough credits to execute, the first admitted transaction will be the earlier received transaction.

#### Exit Behavior
The transaction will exit the semaphore after the coroutine is completed. This is independent of the credit refunding, which is performed later after `refund_time` seconds.

#### Exception Behavior
If the coroutine throws an `Exception`, we will assume the credit has already been consumed and will be refunded after `refund_time` seconds. The `Exception` is thrown back to the caller.

A sample run
-


```python
import asyncio
from credit_semaphore.async_credit_semaphore import AsyncCreditSemaphore

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
```

Output:
```
TXN 1 acquiring CreditSemaphore
TXN 1 entered CreditSemaphore...
2022-10-08 10:51:32.835343::getTick processing 1 takes 3 seconds
TXN 2 acquiring CreditSemaphore
TXN 3 acquiring CreditSemaphore
TXN 4 acquiring CreditSemaphore
TXN 5 acquiring CreditSemaphore
TXN 6 acquiring CreditSemaphore
2022-10-08 10:51:35.838601::getTick processed 1
TXN 1 exits CreditSemaphore, schedule refund in 10...
TXN 2 entered CreditSemaphore...
2022-10-08 10:51:45.848903::getOHLCV processing 2 takes 1 seconds
TXN 4 entered CreditSemaphore...
2022-10-08 10:51:45.848992::getPrice processing 4 takes 4 seconds
2022-10-08 10:51:46.850197::getOHLCV processed 2
TXN 2 exits CreditSemaphore, schedule refund in 10...
2022-10-08 10:51:49.850880::getPrice processed 4
TXN 4 exits CreditSemaphore, schedule refund in 10...
TXN 3 entered CreditSemaphore...
2022-10-08 10:51:56.854937::getOHLCV processing 3 takes 5 seconds
2022-10-08 10:52:01.857848::getOHLCV processed 3
TXN 3 exits CreditSemaphore, schedule refund in 10...
TXN 5 entered CreditSemaphore...
2022-10-08 10:52:11.867476::getTick processing 5 takes 5 seconds
TXN 6 entered CreditSemaphore...
2022-10-08 10:52:11.867588::getTick processing 6 takes 1 seconds
2022-10-08 10:52:12.868778::getTick processed 6
TXN 6 exits CreditSemaphore, schedule refund in 10...
2022-10-08 10:52:16.872035::getTick processed 5
TXN 5 exits CreditSemaphore, schedule refund in 10...
```

Cleaner Usage
-----
Convenience functions are written for possible usage in service class wrappers that are responsible for interfacing with some external API. We allow this access with the decorator `@consume_credits`, which take the parameters

- `costs`: same as `credits`
- `refund_in`: same as `refund_time` 
- `attrname`: (str) the variable name of the credit semaphore object, defaults to `credit_semaphore' 
- `verbose`: (bool) defaults to True, same as before
- `timeout`: to deal with the scenario where a costly transaction sits behind multiple cheap transactions rapidly being submitted to the semaphore, we can optionally add a timeout to our transaction. This raises `asyncio.TimeoutError` if our transaction takes more than the specified number of seconds to complete. Can also be used to timeout unstable network requests which are not responsive and hangs. Defaults to 0 (no timeout).

#### Sample
```python
import asyncio

from datetime import datetime

from credit_semaphore.semutils import consume_credits
from credit_semaphore.async_credit_semaphore import AsyncCreditSemaphore

class DbService():

    def __init__(self):
        self.mysem = AsyncCreditSemaphore(40)
        self.anothersem = AsyncCreditSemaphore(40)

    #uses credit semaphore mysem
    @consume_credits(costs=20, refund_in=10, attrname="mysem")
    async def getTick(self, work, id):
        print(f"{datetime.now()}::getTick processing {id} takes {work} seconds")
        await asyncio.sleep(work)
        print(f"{datetime.now()}::getTick processed {id}")
        return True

    #uses a different credit semaphore
    @consume_credits(costs=30, refund_in=10, timeout=60, attrname="anothersem")
    async def getOHLCV(self, work, id):
        print(f"{datetime.now()}::getOHLCV processing {id} takes {work} seconds")
        await asyncio.sleep(work)
        print(f"{datetime.now()}::getOHLCV processed {id}")
        return True

    #this is not tracked by the semaphore!
    async def getPrice(self, work, id):
        print(f"{datetime.now()}::getPrice processing {id} takes {work} seconds")
        await asyncio.sleep(work)
        print(f"{datetime.now()}::getPrice processed {id}")
        return True

async def main():
    tester = DbService()
    transactions = [
        tester.getOHLCV(work=1, id=1),
        tester.getTick(work=4, id=2),
        tester.getTick(work=1, id=3),
        tester.getTick(work=5, id=4)
    ]
    results = await asyncio.gather(*transactions)

    try:
        transactions = [
            tester.getOHLCV(work=61, id=1)
        ]
        results = await asyncio.gather(*transactions)

    except asyncio.TimeoutError as err:
        print(err)
        print("batch is terminated")
        
if __name__ == "__main__":
    asyncio.run(main())
```

Technical Notes & Best Practices
-----
- Wrap unstable networks and expensive tasks in a timeout transaction. This is to prevent the coroutine from 'await'-ing forever.

- Since the transaction does not know when the coroutine actually performs the credit-costing request, the coroutine passed in to the `transact` function or decorated with the `@consume_credits` should be closest to the costful logic as possible. It should not perform heavy compute or multiple requests so that the credits can refunded as quickly as possible for efficiency. 

- Functions that call credit consuming functions should not be decorated with `@consume_credits` to avoid double counting.

- For a timeout transaction that does not get a chance to run due to it sitting behind other transactions that are opportunistically processed, a `RuntimeWarning: Enable tracemalloc to get the object allocation traceback` may be seen together with the `asyncio.TimeoutError`. This is because the transact contains the coroutine, and the transact is wrapped in an asyncio `task`. If it is unable to enter the semaphore by timeout, the coroutine is never awaited and complains when garbage collected. This is a non-issue. If the timeout occurs after the coroutine has acquired the semaphore, this warning will not be seen but the `asyncio.TimeoutError` will still be thrown.

- The `transact` function only takes in coroutines, and not other `awaitable` objects. This is because our semaphore is not `task`-safe, since `task` runs on iteration of the event loop while the desired behavior is only for the coroutine to be put on the event loop after acquiring the semaphore. 

## Happy Throttling!