import json
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import asyncpg
from fastapi import Depends, FastAPI, Request, Response

from pgqueuer.db import AsyncpgPoolDriver
from pgqueuer.queries import Queries


def get_pgq_queries(request: Request) -> Queries:
    """Retrieve Queries instance from FastAPI app context."""
    return request.app.extra["pgq_queries"]


def create_app() -> FastAPI:
    """
    Create and configure a FastAPI app with a lifespan context manager
    to handle database connection.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        """Manage async database connection throughout the app's lifespan."""
        async with asyncpg.create_pool() as pool:
            app.extra["pgq_queries"] = Queries(AsyncpgPoolDriver(pool))
            yield

    app = FastAPI(lifespan=lifespan)

    @app.get("/reset_password_email")
    async def reset_password_email(
        user_name: str,
        queries: Queries = Depends(get_pgq_queries),
    ) -> Response:
        """Enqueue a job to reset a user's password, identified by user_name."""
        await queries.enqueue(
            "reset_email_by_user_name",
            payload=json.dumps({"user_name": user_name}).encode(),
        )
        return Response(status_code=201)

    @app.post("/enqueue")
    async def enqueue_job(
        entrypoint: str,
        payload: str,
        priority: int = 0,
        queries: Queries = Depends(get_pgq_queries),
    ) -> dict:
        ids = await queries.enqueue(entrypoint, payload.encode(), priority)
        return {"job_ids": ids}

    @app.get("/queue-size")
    async def get_queue_size(
        queries: Queries = Depends(get_pgq_queries),
    ) -> list:
        stats = await queries.queue_size()
        return [
            {
                "entrypoint": s.entrypoint,
                "priority": s.priority,
                "status": s.status,
                "count": s.count,
            }
            for s in stats
        ]

    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(create_app())
