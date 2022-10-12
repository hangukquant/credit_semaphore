import time
import threading

from threading import Lock
from threading import Condition

#BETA
class SyncCreditSemaphore():

    def __init__(self, credits=1):
        if credits < 0:
            raise ValueError("semaphore initial credits must be >= 0")
        self._cond = Condition(Lock())
        self._credits = credits

    def __repr__(self):
        res = super().__repr__()
        return f"has credits {self._credits}."

    def transact(self, lambda_func, credits, refund_time, transaction_id=None, verbose=False):
        if verbose: 
            print(f"TXN {transaction_id} acquiring CreditSemaphore")
        self.acquire(credits, refund_time)

        if verbose: 
            print(f'TXN {transaction_id} entered CreditSemaphore...')
        try:
            result = lambda_func()
        except Exception as err:
            raise err
        finally:
            thread = threading.Thread(target=self.refund_later, args=(credits, refund_time), daemon=True)
            thread.start()
        
        if verbose: 
            print(f'TXN {transaction_id} exits CreditSemaphore, schedule refund in {refund_time}...')
        return result

    def refund_later(self, credits, after_time):
        assert(after_time >= 0)
        time.sleep(after_time)
        self.release(credits)
        return

    def acquire(self, require_credits, refund_time):
        rc = False
        endtime = None
        with self._cond:
            while self._credits < require_credits:
                self._cond.wait(timeout=None)
            else:
                self._credits -= require_credits
                rc = True
        return rc

    def release(self, taken_credits):
        with self._cond:
            self._credits += taken_credits
            self._cond.notify_all()
        return