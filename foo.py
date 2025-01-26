import asyncio

import asyncpg

from pgqueuer import AsyncpgDriver, Queries


async def main() -> None:
    rows = await Queries(AsyncpgDriver(await asyncpg.connect())).time_in_queue_stats()
    for row in rows:
        print(row)


asyncio.run(main())
