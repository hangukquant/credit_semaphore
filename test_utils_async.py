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
    @consume_credits(costs=30, refund_in=10, timeout=60, attrname="mysem")
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
            tester.getTick(work=61, id=1),
            tester.getTick(work=61, id=2),
            tester.getTick(work=61, id=3),
            tester.getOHLCV(work=1, id=4)
           
        ]
        results = await asyncio.gather(*transactions)

    except asyncio.TimeoutError as err:
        print(err)
        print("second batch is terminated")
        
    try:
        transactions = [
            tester.getOHLCV(work=61, id=1)
        ]
        results = await asyncio.gather(*transactions)

    except asyncio.TimeoutError as err:
        print(err)
        print("third batch is terminated")
        
if __name__ == "__main__":
    asyncio.run(main())