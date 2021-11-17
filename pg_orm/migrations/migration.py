import asyncio
import logging
import json
from pathlib import Path
import psycopg2
import asyncpg
from typing import Union, Type

from pg_orm.models.base_model import Model, AsyncModel
from pg_orm.migrations.schema_diff import SchemaDifference


log = logging.getLogger(__name__)
loop = asyncio.get_event_loop()


def _get_data_file(cls: Union[Type[Model], Type[AsyncModel]], directory):
    return Path(f"{directory}\\{cls.__name__}.json")


def _write_migrations(cls: Union[Type[Model], Type[AsyncModel]], directory="migrations"):
    """Writes the data to the data files, creates it if not exists
       WARNING: Do not manually call this function unless you know what you are doing use migrate instead"""
    data_file = _get_data_file(cls, directory)

    table_data = cls.to_dict()

    if not data_file.exists():
        data_file.parent.mkdir(parents=True, exist_ok=True)
        with data_file.open("w+", encoding="utf-8") as fp:
            json.dump(table_data, fp, indent=4, ensure_ascii=True)

    else:
        with data_file.open("w", encoding="utf-8") as fp:
            json.dump(table_data, fp, indent=4, ensure_ascii=True)


def migrate(cls: Type[Model], directory="migrations", print_query: bool = False):
    data_file = _get_data_file(cls, directory)

    if not data_file.exists():
        _write_migrations(cls, directory)
        return cls.create_table()

    with data_file.open() as fp:
        data = json.load(fp)

        try:
            cls.db.execute(f"SELECT * FROM {data['name']};")
        except psycopg2.errors.UndefinedTable:
            cls.create_table()
            _write_migrations(cls, directory)
            return

        statements = SchemaDifference(cls, data).to_sql()

        if statements:
            for statement in statements:
                cls.db.execute(statement.strip())
                if print_query:
                    print(statement + "\n")
        else:
            print("No changes to apply")

    _write_migrations(cls, directory)  # At last synchronize the json files with the current state of the Model


def migrate_all(directory="migrations", print_query: bool = False):
    for model in Model.__subclasses__():
        migrate(model, directory, print_query)


async def async_migrate(cls: Type[AsyncModel], directory="migrations", print_query: bool = False):
    data_file = _get_data_file(cls, directory)

    if not data_file.exists():
        _write_migrations(cls, directory)
        return await cls.create_table()

    with data_file.open() as fp:
        data = json.load(fp)

        try:
            await cls.db.execute(f"SELECT * FROM {data['name']};")
        except asyncpg.exceptions.UndefinedTableError:
            await cls.create_table()
            return _write_migrations(cls, directory)

        statements = SchemaDifference(cls, data).to_sql()

        if statements:
            for statement in statements:
                await cls.db.execute(statement.strip())
                if print_query:
                    print(statement + "\n")
        else:
            print("No changes to apply")

    _write_migrations(cls, directory)  # At last synchronize the json files with the current state of the Model


async def async_migrate_all(directory="migrations", print_query: bool = False):
    for model in AsyncModel.__subclasses__():
        await async_migrate(model, directory, print_query)
