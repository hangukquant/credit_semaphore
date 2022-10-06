import asyncio
import functools
import collections

class AsyncCreditSemaphore():
    def __init__(self, credits=1):
        if credits < 0:
            raise ValueError("Semaphore credit value must be >= 0")
        self._waiters = None
        self._credits = credits
        self._future_costs = {}
        self._future_refunds = {}

    def __repr__(self):
        res = super().__repr__()
        return f"has credits {self._credits} and waiter count of {0 if not self._waiters else len(self._waiters)}."

    async def transact(self, coroutine, credits, refund_time, transaction_id=None, verbose=False):
        assert(asyncio.iscoroutine(coroutine))
        
        if verbose: 
            print(f"TXN {transaction_id} acquiring CreditSemaphore")
        await self.acquire(credits, refund_time)

        if verbose: 
            print(f'TXN {transaction_id} entered CreditSemaphore...')
        try:
            result = await coroutine
        except Exception as err:
            raise err
        finally:
            self.refund_later(credits, refund_time)
        
        if verbose: 
            print(f'TXN {transaction_id} exits CreditSemaphore, schedule refund in {refund_time}...')
        return result

    def refund_later(self, credits, after_time):
        assert(after_time >= 0)
        if after_time == 0:
            self.release(credits)
        else:
            asyncio.get_running_loop().call_later(
                after_time,
                functools.partial(self.release, credits)
            )
        return

    def locked(self, require_credits):
        return self._credits < require_credits or (
            any(not w.cancelled() for w in (self._waiters or ())))

    async def acquire(self, require_credits, refund_time):
        if not self.locked(require_credits):
            self._credits -= require_credits
            return True

        if self._waiters is None:
            self._waiters = collections.deque()
        
        fut = asyncio.get_event_loop().create_future()
        self._waiters.append(fut)
        self._future_costs[fut] = require_credits
        self._future_refunds[fut] = refund_time

        try:
            try:
                await fut
            finally:
                del self._future_costs[fut]
                del self._future_refunds[fut]
                self._waiters.remove(fut)

        except Exception as err:
            if not fut.cancelled():
                self.refund_later(self._future_costs[fut], self._future_refunds[fut])
                del self._future_costs[fut]
                del self._future_refunds[fut]
            raise

        self._wake_up_next()
        return True

    def release(self, taken_credits):
        self._credits += taken_credits
        self._wake_up_next()

    def _wake_up_next(self):
        if not self._waiters:
            return

        for fut in self._waiters:
            if not fut.done() and self._credits >= self._future_costs[fut]:
                self._credits -= self._future_costs[fut]
                fut.set_result(True)
                return