import asyncio
import logging
from pg_orm.models.base_model import Model, AsyncModel

try:
    from psycopg2.pool import AbstractConnectionPool
except ImportError:
    AbstractConnectionPool = None

try:
    from asyncpg import Pool
except ImportError:
    Pool = None

log = logging.getLogger(__name__)


async def apply_async_migrations(pool):
    async with pool.acquire() as conn:
        for model in AsyncModel.__subclasses__():
            log.debug(f"Creating table for model {model.__class__.__name__}")
            model.create_table(conn)
            log.debug(f"Created table for model {model.__class__.__name__}")
    await pool.release(conn)


def apply_migrations(pool, sync_migrations=False, async_migrations=False):
    """Makes tables for the models"""
    if sync_migrations:
        if not isinstance(pool, AbstractConnectionPool):
            raise TypeError(
                "Pool must be instance of psycopg2.pool.AbstractConnectionPool"
            )
        with pool.getconn() as conn:
            for model in Model.__subclasses__():
                log.debug(f"Creating table for model {model.__class__.__name__}")
                model.create_table(conn)
                log.debug(f"Created table for model {model.__class__.__name__}")
        pool.putconn(conn)

    if async_migrations:
        if not isinstance(pool, Pool):
            raise TypeError("Pool must be instance of asyncpg.Pool")
        for model in AsyncModel.__subclasses__():
            run = asyncio.get_event_loop().run_until_complete
            run(apply_async_migrations(pool))
