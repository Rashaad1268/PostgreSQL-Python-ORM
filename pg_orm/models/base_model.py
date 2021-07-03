try:
    import asyncpg
except ImportError:
    asyncpg = None
try:
    import psycopg2
    from psycopg2 import pool
except ImportError:
    psycopg2 = None
    pool = None

import traceback
import typing as t
import logging

from pg_orm.errors import FiledError
from pg_orm.models.fields import Field, AutoIncrementIDField
from pg_orm.models.manager import Manager, AsyncManager
from pg_orm.models.database import Psycopg2Driver, AsyncpgDriver


log = logging.getLogger(__name__)


class ModelBase(type):
    def __new__(cls, name, bases, attrs, **kwargs):
        model_fields = []
        table_name = attrs.get("__tablename__", name)
        new_attrs = dict()

        if not attrs.get("id", None):
            new_attrs["id"] = AutoIncrementIDField()

        for k, v in attrs.items():
            new_attrs[k] = v

        for key, val in new_attrs.items():
            if isinstance(val, Field):
                model_fields.append(val)
                setattr(val, "column_name", key)

        new_attrs["table_name"] = table_name
        new_attrs["fields"] = model_fields
        new_attrs["_valid_fields"] = [field.column_name for field in model_fields]

        new_class = super().__new__(cls, name, bases, new_attrs)

        if new_class._is_sync:
            Manager(new_class)
        elif not new_class._is_sync:
            AsyncManager(new_class)

        return new_class


class Model(metaclass=ModelBase):
    _is_sync = True

    def __init__(self, **kwargs):
        self.attrs = kwargs

        for key, val in kwargs.items():
            if key not in self._valid_fields:
                raise FiledError(key, self._valid_fields)
            else:
                setattr(self, key, val)
        
        if not psycopg2:
            raise ModuleNotFoundError("Need to install psycopg2 for synchronous usage")

    @classmethod
    def drop(cls):
        """Drops the table"""
        cls.db.execute(f"DROP TABLE {cls.table_name};")

    @classmethod
    def create_table(cls, conn):
        """Creates the table for the model"""
        log.info(f"Creating table for Model '{cls.table_name}'")
        columns = [f"{field.column_name} {field.to_sql()}" for field in cls.fields]
        query = """
                CREATE TABLE IF NOT EXISTS %s (
                    %s
                )""" % (
            cls.table_name,
            ",\n".join(columns),
        )

        with conn.cursor() as cursor:
            cursor.execute(query)
            conn.commit()

    def save(self, commit: bool = True):
        """Saves the current model instace to the database"""
        attrs = self.attrs.copy()
        attrs.pop("id", None)  # The id will be automatically set
        table_name = self.table_name
        col_string = ", ".join(attrs.keys())
        param_string = ", ".join("%s" for _ in range(len(attrs.keys())))
        query = f"INSERT INTO {table_name} ({col_string}) VALUES({param_string})"

        self.db.execute(query, *tuple(attrs.values()), commit=commit)

    def delete(self, commit: bool = True):
        """Deletes the current model instance from the database"""
        id = self.attrs.get("id", None)
        query = f"DELETE FROM {self.table_name} WHERE Id=%s;"
        self.db.execute(query, id, commit=commit)

    def update(self, commit: bool = True):
        """Updates the model instace in the database with the current instance"""
        attrs = self.attrs
        id = attrs.get("id", None)
        new_values = ", ".join([f"{k}=%s" for k in attrs.keys()])
        query = f"UPDATE {self.table_name} SET {new_values} WHERE Id=%s"
        self.db.execute(query, *tuple(attrs.values()), id, commit=commit)

    def __repr__(self):
        return "<%s: %s>" % (
            self.__class__.__name__,
            ", ".join([f"{k}={v!r}" for k, v in self.attrs.items()]),
        )

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, Model) and self.id == other.id

    def __setattr__(self, name, value):
        if str(name) in self._valid_fields:
            self.attrs[name] = value
            object.__setattr__(self, name, value)
        else:
            object.__setattr__(self, name, value)

    def __ne__(self, other):
        return not self.__eq__(other)


def create_model(
    pg_pool: t.Union[pool.AbstractConnectionPool, asyncpg.Pool],
    cls=Model,
    adapter_cls=Psycopg2Driver,
):
    cls.db = adapter_cls(pg_pool)

    return cls


class AsyncModel(metaclass=ModelBase):
    """This is the model class which needs to be subclassed to use the async orm"""

    _is_sync = False

    def __init__(self, **kwargs):
        self.attrs = kwargs

        for key, val in kwargs.items():
            if key not in self._valid_fields:
                raise FiledError(key, self._valid_fields)
            else:
                setattr(self, key, val)
            
        if not asyncpg:
            raise ModuleNotFoundError("Need to install asyncpg for asynchronous usage")

    @classmethod
    async def create_table(cls, conn):
        """Creates the table for the model if it doesn't exist"""
        log.info(f"Creating table for Model '{cls.table_name}'")
        columns = [f"{field.column_name} {field.to_sql()}" for field in cls.fields]
        query = """
                CREATE TABLE IF NOT EXISTS %s (
                    %s
                )""" % (
            cls.table_name,
            ",\n".join(columns),
        )

        await conn.execute(query)

    @classmethod
    async def drop(cls):
        """Drops the table for the model"""
        await cls.db.execute(f"DROP TABLE {cls.table_name};")

    async def save(self, commit: bool = True):
        """Saves the current model instance"""
        attrs = self.attrs.copy()
        attrs.pop("id", None)  # The id will be automatically set
        col_string = ", ".join(attrs.keys())
        param_string = ", ".join("%s" for _ in range(len(attrs.keys())))
        query = f"INSERT INTO {self.table_name} ({col_string}) VALUES({param_string})"

        await self.db.execute(query, *tuple(attrs.values()))

    async def delete(self):
        """Deletes the current model instance"""
        id = self.attrs.get("id", None)
        query = f"DELETE FROM {self.table_name} WHERE Id=$1;"
        await self.db.execute(query, id)

    async def update(self):
        """Updates the model instace in the database with the current instance"""
        attrs = self.attrs.copy()
        id = attrs.pop("id", None)
        count = 1
        new_values = []
        for key in attrs.keys():
            new_values.append(f"{key}=${count}")
            count += 1
        new_values = ", ".join(new_values)
        query = f"UPDATE {self.table_name} SET {new_values} WHERE Id=${count}"
        await self.db.execute(query, *tuple(attrs.values()), id)

    def __repr__(self):
        return "<%s: %s>" % (
            self.__class__.__name__,
            ", ".join([f"{k}={v!r}" for k, v in self.attrs.items()]),
        )

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, Model) and self.id == other.id

    def __setattr__(self, name, value):
        if str(name) in self._valid_fields:
            self.attrs[name] = value
            object.__setattr__(self, name, value)
        else:
            object.__setattr__(self, name, value)

    def __ne__(self, other):
        return not self.__eq__(other)


def create_async_model(pg_pool: asyncpg.Pool):
    return create_model(pg_pool, cls=AsyncModel, adapter_cls=AsyncpgDriver)
