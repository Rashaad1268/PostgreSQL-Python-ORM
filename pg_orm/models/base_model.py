import typing as t
import pydoc
from pathlib import Path
import logging
import os
import collections

from pg_orm.errors import FiledError, DataBaseNotConfigured
from pg_orm.models.fields import Field, AutoIncrementIntegerField
from pg_orm.models.manager import Manager, AsyncManager
from pg_orm.models.query_generator import QueryGenerator
from pg_orm.models.database import Psycopg2Driver, AsyncpgDriver
from pg_orm.models.utils import maybe_await

log = logging.getLogger(__name__)


class ModelMeta(type):
    def __new__(cls, name, bases, attrs, **kwargs):
        if BaseModel in bases:
            return super().__new__(cls, name, bases, attrs)

        table_name = (
                attrs.pop("__tablename__", None)
                or attrs.pop("table_name", None)
                or kwargs.get("__tablename__")
                or kwargs.get("table_name")
        )
        if table_name is None:
            raise Exception("Table name not spcified.")

        model_fields = collections.OrderedDict()

        for key, val in attrs.items():
            if isinstance(val, Field):
                model_fields[key] = val
                val.column_name = key

        if not model_fields:
            raise Exception("No fields specified")

        if not any(field.primary_key for field in model_fields.values()):
            id_field = AutoIncrementIntegerField()
            id_field.column_name = "id"
            model_fields["id"] = id_field
            model_fields.move_to_end("id", last=False)

        attrs["table_name"] = table_name
        attrs["fields"] = model_fields

        new_class = super().__new__(cls, name, bases, attrs)
        new_class._query_gen = QueryGenerator(new_class)
        model_is_sync = getattr(new_class, "_is_sync")

        if model_is_sync:
            new_class.objects = Manager(new_class)
        elif not model_is_sync:
            new_class.objects = AsyncManager(new_class)

        return new_class


class BaseModel:
    db: t.Union[Psycopg2Driver, AsyncpgDriver, None] = None
    attrs: t.Dict[str, t.Any]
    fields: t.Dict[str, Field]
    table_name: str

    """Contains common method for Model and AsyncModel"""
    def __init__(self, **kwargs):
        super().__setattr__("attrs", kwargs)

        if super().__getattribute__("db") is None:
            raise DataBaseNotConfigured()

        for key in kwargs:
            if key not in self.fields:
                raise FiledError(key, self.fields.keys())

    @classmethod
    def set_db(cls, db):
        cls.db = db

    @classmethod
    def to_dict(cls):
        data = dict()
        data["name"] = cls.table_name
        data["path"] = cls.__module__ + "." + cls.__qualname__
        data["fields"] = [f.to_dict() for f in cls.fields.values()]
        return data

    @classmethod
    def from_dict(cls, data):
        path = data["path"]
        given = cls.__module__ + '.' + cls.__qualname__
        if given != path:
            cls = pydoc.locate(path)
            if cls is None:
                raise RuntimeError('Could not locate "%s"' % path)

        self = cls()
        self.table_name = data["name"]
        self.fields = {field["column_name"]: Field.from_dict(field) for field in data["fields"]}
        return self

    @classmethod
    def _delete_migration_files(cls, directory="migrations"):
        data_file = Path(os.path.join(directory, f"{cls.__name__}.json"))

        if not data_file.exists():
            raise RuntimeError("Could not find the appropriate migrations files.")

        try:
            data_file.unlink()
        except Exception:
            raise RuntimeError("Could not delete migration files.")

    def __repr__(self):
        return "<%s: %s>" % (
            type(self).__name__,
            ", ".join(f"{k}={v!r}" for k, v in self.attrs.items()),
        )

    def __hash__(self):
        return hash(self.attrs.get("id"))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id

    def __setattr__(self, name, value):
        if name in self.fields.keys():
            self.attrs[name] = value
        else:
            super().__setattr__(name, value)

    def __getattribute__(self, item):
        attrs = super().__getattribute__("attrs")
        if item in attrs:
            return attrs[item]
        else:
            return super().__getattribute__(item)

    def __ne__(self, other):
        return not self.__eq__(other)


class Model(BaseModel, metaclass=ModelMeta):
    """The base class for all models."""
    @classmethod
    @property
    def _is_sync(cls):
        return True

    @classmethod
    def create_table(cls):
        """Creates the table for the model"""
        log.info(f"Creating table '{cls.table_name}'")
        cls.db.execute(cls._query_gen.generate_table_creation_query())

    @classmethod
    def drop(cls, directory="migrations", delete_migration_files: bool = True):
        """Drops the table and deletes the data files"""
        if delete_migration_files:
            cls._delete_migration_files(directory)

        cls.db.execute(f"DROP TABLE {cls.table_name} CASCADE;")

    def save(self, commit: bool = True):
        """Saves the current model instance to the database"""
        for key, value in self.attrs.items():
            for validator in self.fields[key].validators:
                maybe_await(validator(value))

        all_fields = set(self.fields)
        all_fields.discard("id")
        unspecified_fields = set(all_fields) - set(self.attrs)
        for field_name in unspecified_fields:
            field = self.fields[field_name]
            if field.default is not None:
                self.attrs[field_name] = field._get_default_python_val()

        query, values = self._query_gen.generate_insert_query(**self.attrs, return_inserted=True)
        data = self.db.fetchone(query, *values, commit=commit)
        self.attrs.update(**data)

    def delete(self, commit: bool = True):
        """Deletes the current model instance from the database"""
        query, id = self._query_gen.generate_row_deletion_query(**self.attrs)
        self.db.execute(query, id, commit=commit)

    def update(self, commit: bool = True):
        """Updates the model instace in the database with the current instance"""
        query, args, id = self._query_gen.generate_update_query(**self.attrs)
        self.db.execute(query, *args, id, commit=commit)


class AsyncModel(BaseModel, metaclass=ModelMeta):
    """This is the model class which needs to be subclassed to use the async orm"""

    @classmethod
    @property
    def _is_sync(cls):
        return False

    @classmethod
    async def create_table(cls):
        """Creates the table for the model if it doesn't exist"""
        log.info(f"Creating table for Model '{cls.table_name}'")
        await cls.db.execute(cls._query_gen.generate_table_creation_query())

    @classmethod
    async def drop(cls, directory="migrations", delete_migration_files: bool = True):
        """Drops the table and deletes the data files"""
        if delete_migration_files:
            cls._delete_migration_files(directory)

        await cls.db.execute(f"DROP TABLE {cls.table_name} CASCADE;")

    async def save(self):
        """Saves the current model instance"""
        for key, value in self.attrs.items():
            for validator in self.fields[key].validators:
                maybe_await(validator(value))

        all_fields = set(self.fields)
        all_fields.discard("id")
        unspecified_fields = set(all_fields) - set(self.attrs)
        for field_name in unspecified_fields:
            field = self.fields[field_name]
            if field.default is not None:
                self.attrs[field_name] = field._get_default_python_val()

        query, values = self._query_gen.generate_insert_query(asyncpg=True, **self.attrs)

        await self.db.execute(query, *values)

    async def delete(self):
        """Deletes the current model instance"""
        query, id = self._query_gen.generate_row_deletion_query(True, **self.attrs)
        await self.db.execute(query, id)

    async def update(self):
        """Updates the model instace in the database with the current instance"""
        query, args, id = self._query_gen.generate_update_query(True, **self.attrs)
        await self.db.execute(query, *args, id)
