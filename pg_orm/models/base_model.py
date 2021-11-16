from psycopg2 import pool
import asyncpg
from copy import deepcopy
import typing as t
import pydoc
import logging

import pg_orm 
from pg_orm.errors import FiledError
from pg_orm.models.fields import Field, AutoIncrementIDField
from pg_orm.models.manager import Manager, AsyncManager
from pg_orm.models.query_generator import QueryGenerator
from pg_orm.models.database import Psycopg2Driver, AsyncpgDriver


log = logging.getLogger(__name__)

def _delete_migration_files(cls, directory="migrations"):
    from pathlib import Path
    data_file = Path(f"{directory}\\{cls.__name__}.json")

    if not data_file.exists():
        raise RuntimeError("Could not find the appropriate data files.")

    try:
        data_file.unlink()
    except:
        raise RuntimeError("Could not delete current migration file")


class ModelBase(type):
    def __new__(cls, name, bases, attrs, **kwargs):
        table_name = (
            attrs.pop("__tablename__", None)
            or attrs.pop("table_name", None)
            or kwargs.get("__tablename__", None)
            or kwargs.get("table_name", None)
        )
        if table_name is None:
            raise Exception("Table name not spcified.")
        
        model_fields = []
        new_attrs = dict()

        if attrs.get("id") is None:
            new_attrs["id"] = AutoIncrementIDField()

        for k, v in attrs.items():
            new_attrs[k] = v

        for key, val in new_attrs.items():
            if isinstance(val, Field):
                model_fields.append(val)
                setattr(val, "column_name", key)
            
        if not model_fields:
            raise Exception("Fields not specified")

        new_attrs["table_name"] = table_name
        new_attrs["fields"] = tuple(model_fields)
        new_attrs["_valid_fields"] = tuple(map(lambda field: field.column_name, model_fields))

        new_class = super().__new__(cls, name, bases, new_attrs)
        new_class._query_gen = QueryGenerator(new_class)

        if new_class._is_sync:
            Manager(new_class)
        elif not new_class._is_sync:
            AsyncManager(new_class)

        return new_class


class Model(metaclass=ModelBase, table_name="Model"):
    """The base class for all models."""
    db: t.Union[Psycopg2Driver, AsyncpgDriver]
    fields: t.Tuple[Field]
    table_name: str

    @property
    def _is_sync(self):
        return True

    def __init__(self, **kwargs):
        self.attrs = kwargs

        for key, val in kwargs.items():
            if key not in self._valid_fields:
                raise FiledError(key, self._valid_fields)
            else:
                setattr(self, key, val)

    @classmethod
    def set_db(cls, db):
        cls.db = db

    @classmethod
    def to_dict(cls):
        data = dict()
        data["name"] = cls.table_name
        data["__meta__"] = cls.__module__ + "." + cls.__qualname__
        data["fields"] = [f.to_dict() for f in cls.fields]
        return data

    @classmethod
    def from_dict(cls, data):
        meta = data["__meta__"]
        given = cls.__module__ + '.' + cls.__qualname__
        if given != meta:
            cls = pydoc.locate(meta)
            if cls is None:
                raise RuntimeError('Could not locate "%s"' % meta)

        # self = deepcopy(cls)
        self = cls()
        self.table_name = data["name"]
        self.fields = [Field.from_dict(a) for a in data["fields"]]
        return self

    @classmethod
    def create_table(cls):
        """Creates the table for the model"""
        log.info(f"Creating table for Model '{cls.table_name}'")

        cls.db.execute(cls._query_gen.generate_table_creation_query())

    @classmethod
    def drop(cls, directory="migrations", delete_migration_files: bool = True):
        """Drops the table and deletes the data files"""
        if delete_migration_files:
            _delete_migration_files(cls, directory)

        cls.db.execute(f"DROP TABLE {cls.table_name} CASCADE;")

    def save(self, commit: bool = True):
        """Saves the current model instance to the database"""
        query, values = self._query_gen.generate_insert_query(**self.attrs)

        for field in self.fields:
            for validator in field.validators:
                for key, value in self.attrs.items():
                    if field.column_name == key:
                        validator(value)

        self.db.execute(query, *values, commit=commit)

    def delete(self, commit: bool = True):
        """Deletes the current model instance from the database"""
        query, id = self._query_gen.generate_row_deletion_query(**self.attrs)
        self.db.execute(query, id, commit=commit)

    def update(self, commit: bool = True):
        """Updates the model instace in the database with the current instance"""
        query, args, id = self._query_gen.generate_update_query(**self.attrs)
        self.db.execute(query, *args, id, commit=commit)

    def __repr__(self):
        return "<%s: %s>" % (
            self.__class__.__name__,
            ", ".join([f"{k}={v!r}" for k, v in self.attrs.items()]),
        )

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id

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
    cls.set_db(adapter_cls(pg_pool))

    return cls


class AsyncModel(Model, metaclass=ModelBase, table_name="AsyncModel"):
    """This is the model class which needs to be subclassed to use the async orm"""

    @property
    def _is_sync(self):
        return False

    @classmethod
    async def create_table(cls):
        """Creates the table for the model if it doesn't exist"""
        log.info(f"Creating table for Model '{cls.table_name}'")
        await cls.db.execute(cls._query_gen.generate_table_creation_query())

    @classmethod
    async def drop(cls, directory="migrations", delete_migration_files: bool=True):
        """Drops the table and deletes the data files"""
        if delete_migration_files:
            _delete_migration_files(cls, directory)

        await cls.db.execute(f"DROP TABLE {cls.table_name} CASCADE;")

    async def save(self, commit: bool = True):
        """Saves the current model instance"""
        query, values = self._query_gen.generate_insert_query()

        await self.db.execute(query, *values)

    async def delete(self):
        """Deletes the current model instance"""
        id = self.attrs.get("id", None)
        query = f"DELETE FROM {self.table_name} WHERE Id=$1;"
        await self.db.execute(query, id)

    async def update(self):
        """Updates the model instace in the database with the current instance"""
        query, args, id = self._query_gen.generate_update_query(**self.attrs)
        await self.db.execute(query, *args, id)


def create_async_model(pool: asyncpg.Pool):
    return create_model(pool, AsyncModel, AsyncpgDriver)
