import psycopg2
from psycopg2 import pool
import asyncpg


class Psycopg2Driver:
    def __init__(self, pool: pool.AbstractConnectionPool):
        self.pool = pool

    def execute(self, query, *args, commit=True):
        with self.pool.getconn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, args)
                if commit:
                    conn.commit()
                self.pool.putconn(conn)

    def fetchall(self, query, *args):
        query_set = []
        with self.pool.getconn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, args)
                result = cursor.fetchall()
                if result:
                    column_names = [desc[0] for desc in cursor.description]
                    query_set = [dict(zip(column_names, row)) for row in result]

                self.pool.putconn(conn)

        return query_set

    def fetchone(self, query, *args, commit=False):
        query_set = {}
        with self.pool.getconn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, args)
                if commit:
                    conn.commit()
                result = cursor.fetchone()
                if result:
                    column_names = [desc[0] for desc in cursor.description]
                    query_set = dict(zip(column_names, result))
                self.pool.putconn(conn)

        return query_set


class AsyncpgDriver:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def execute(self, query, *args):
        async with self.pool.acquire() as conn:
            result = await conn.execute(query, *args)
            await self.pool.release(conn)

        return result

    async def fetch(self, query, *args):
        async with self.pool.acquire() as conn:
            result = await conn.fetch(query, *args)
            await self.pool.release(conn)

        return result

    async def fetchrow(self, query, *args):
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow(query, *args)
            await self.pool.release(conn)

        return record

    async def fetchval(self, query, *args):
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(query, *args)
            await self.pool.release(conn)

        return result
