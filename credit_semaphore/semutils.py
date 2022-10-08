import asyncio
from functools import wraps

def consume_credits(_func=None, *, costs, refund_in, attrname="credit_semaphore", timeout=0, verbose=True):
    
    def sync_wrapper(func):
        @wraps(func)
        async def connection_handler(self, *args, **kwargs):    
            assert(hasattr(self, attrname))
            assert(costs >= 0)

            sem = getattr(self, attrname)
            transaction = sem.transact(
                coroutine=func(self, *args, **kwargs), 
                credits=costs, 
                refund_time=refund_in, 
                transaction_id={"fn": func.__name__, "args": args, "kwargs": kwargs}, 
                verbose=verbose
            )

            if timeout == 0:
                result = await transaction
            else:
                result = await asyncio.wait_for(asyncio.create_task(transaction), timeout=timeout)
  
            return result
                      
        return connection_handler

    if _func is None:
        return sync_wrapper
    else:
        return sync_wrapper(_func)