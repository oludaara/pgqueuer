from __future__ import annotations

import sys

import asyncpg
import uvloop

from pgqueuer import models
from pgqueuer.db import AsyncpgDriver
from pgqueuer.queries import Queries


async def main(N: int) -> None:
    connection = await asyncpg.connect()
    driver = AsyncpgDriver(connection)
    queries = Queries(driver)
    ids = await queries.enqueue(
        ["fetch"] * N,
        [f"this is from me: {n}".encode() for n in range(1, N + 1)],
        [0] * N,
    )

    def predicate(changes: list[models.Log]) -> bool:
        ids = {c.job_id for c in changes}
        return sum(c.status == "successful" for c in changes) == len(ids)

    await queries.wait_until(ids, predicate=predicate)


if __name__ == "__main__":
    N = 1_000 if len(sys.argv) == 1 else int(sys.argv[1])
    uvloop.run(main(N))
