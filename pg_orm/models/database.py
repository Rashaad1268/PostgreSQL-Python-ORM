from __future__ import annotations

from abc import ABC, abstractmethod
import sqlite3


try:
    import asyncpg
except ModuleNotFoundError:
    asyncpg = None
try:
    from psycopg2.pool import SimpleConnectionPool
except ModuleNotFoundError:
    SimpleConnectionPool = None


class DatabaseWrapper(ABC):
    @property
    @abstractmethod
    def vendor(self):
        pass

    @property
    @abstractmethod
    def queryparam_style(self):
        pass

    @abstractmethod
    def execute(self, *args, **kwargs):
        pass

    @abstractmethod
    def fetchone(self, *args, **kwargs):
        pass

    @abstractmethod
    def fetchall(self, *args, **kwargs):
        pass


class Psycopg2Wrapper(DatabaseWrapper):
    def __init__(self, pool):
        self.pool: SimpleConnectionPool = pool

    @property
    def vendor(self):
        return "postgresql"

    @property
    def queryparam_style(self):
        return "format"

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


class AsyncpgWrapper(DatabaseWrapper):
    def __init__(self, pool):
        self.pool: asyncpg.Pool = pool

    @property
    def vendor(self):
        return "postgresql"

    @property
    def queryparam_style(self):
        return "native_postgresql"

    async def execute(self, query, *args):
        result = await self.pool.execute(query, *args)

        return result

    async def fetchall(self, query, *args):
        result = await self.pool.fetch(query, *args)

        return result

    async def fetchone(self, query, *args):
        result = await self.pool.fetchrow(query, *args)

        return result


class SQLite3Wrapper(DatabaseWrapper):
    def __init__(self, connection):
        self.connection: sqlite3.Connection = connection

        def dict_factory(cursor, row):
            d = {}
            for idx, col in enumerate(cursor.description):
                d[col[0]] = row[idx]
            return d

        self.connection.row_factory = dict_factory

    @property
    def vendor(self):
        return "sqlite"

    @property
    def queryparam_style(self):
        return "qmark"

    def execute(self, query, *args, commit=True):
        with self.connection.cursor() as cursor:
            cursor.execute(query, *args)
            if commit:
                self.connection.commit()

    def fetchall(self, query, *args):
        with self.connection.cursor() as cursor:
            cursor.execute(query, *args)
            return cursor.fetchall()

    def fetchone(self, query, *args):
        with self.connection.cursor() as cursor:
            cursor.execute(query, *args)
            return cursor.fetchone()
