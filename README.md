# credit_semaphore
Asynchronous Semaphore Based on Credits for Efficient Credit-Based API Throttling
========

This library provides an asynchronous semaphore that generalizes the asyncio semaphore to handle rate limiting using a credit based system. A common use case is in API throttling.

Usage
-----
A simple interface is provided for the credit semaphore.

```python
async def transact(self, coroutine, credits, refund_time, transaction_id=None, verbose=False):
    ...
```
The credit semaphore has a `transact` asynchronous function that takes in 3 key parameters

- coroutine: the coroutine to run, for instance `asyncio.sleep(1)`.
- credits: the number of credits (float or integer) the coroutine costs.
- refund_time: the time in seconds it takes for the credits to be returned to the semaphore.
- transaction_id (optional): this is an identifier for the transaction, and can be used with `verbose=True` for printing out when a particular transaction acquires and releases the semaphore.
- verbose (optional): prints to terminal the transaction status when acquiring and releasing the semaphore.

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
The transaction will exit the semaphore after the coroutine is completed. This is independent of the credit refunding, and if the transaction fails downstream, this will not affect the refund.

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