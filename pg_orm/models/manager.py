try:
    import psycopg2
except ImportError:
    psycopg2 = None
try:
    import asyncpg
except ImportError:
    asyncpg = None

from pg_orm import models
from pg_orm.models.queryset import QuerySet


class Manager:
    def __init__(self, model):
        model.objects = self
        self.model = model
        self.db = getattr(model, "db", None)

    def all(self) -> QuerySet:
        """Returns all rows in the table"""
        query = "SELECT * FROM {0};".format(self.model.table_name)
        return QuerySet(
            self.model, [self._return_model(row) for row in self.db.fetchall(query)]
        )

    def get(self, id=None, **kwargs):
        """Returns a single row with the given values"""
        self.model(**kwargs)
        if id:
            query = "SELECT * FROM {0} WHERE Id=%s;".format(self.model.table_name)
            return self._return_model(self.db.fetchone(query, (id,)))
        else:
            params = [f"{key}=%s" for key in kwargs.keys()]
            query = "SELECT * FROM {0} WHERE {1};".format(
                self.model.table_name, " AND ".join(params)
            )
            return self._return_model(self.db.fetchone(query, *tuple(kwargs.values())))

    def filter(self, **kwargs) -> QuerySet:
        """Similar to get but returns multiple rows if exists"""
        self.model(**kwargs)
        params = [f"{key}=%s" for key in kwargs.keys()]
        query = "SELECT * FROM {0} WHERE {1};".format(
            self.model.table_name, " AND ".join(params)
        )
        return QuerySet(
            self.model,
            [
                self._return_model(row)
                for row in self.db.fetchall(query, *tuple(kwargs.values()))
            ],
        )

    def search(self, **kwargs) -> QuerySet:
        """Runs a SQL search query with the given values"""
        self.model(**kwargs)
        params = [f"{key} LIKE %s" for key in kwargs.keys()]
        query = "SELECT * FROM {0} WHERE {1};".format(
            self.model.table_name, " AND ".join(params)
        )
        arguments = dict()
        for key, value in kwargs.items():
            arguments[key] = f"%{value}%"

        return QuerySet(
            self.model,
            [
                self._return_model(row)
                for row in self.db.fetchall(query, *tuple(arguments.values()))
            ],
        )

    def create(self, **kwargs):
        """
        Creates and returns new model instance with the given values and saves it in the database
        """
        self.model(**kwargs)
        table_name = self.model.table_name
        col_string = ", ".join(kwargs.keys())
        param_string = ", ".join("%s" for _ in range(len(kwargs.keys())))
        query = f"INSERT INTO {table_name} ({col_string}) VALUES({param_string}) RETURNING Id;"

        values = []
        for v in kwargs.values():
            if isinstance(v, models.base_model.Model):
                values.append(v.id)
            else:
                values.append(v)

        for field in self.model.fields:
            for validator in field.data_validators:
                for key, value in kwargs.items():
                    if field.column_name == key:
                        validator(value)

        instance_id = self.db.fetchval(query, *tuple(values))["id"]

        kwargs["id"] = instance_id
        return self.model(**kwargs)

    def _return_model(self, query_set: dict):
        if bool(query_set):
            return self.model(**query_set)
        else:
            return None


class AsyncManager(Manager):
    def __init__(self, model):
        model.objects = self
        self.model = model
        self.db = getattr(model, "db", None)

    async def all(self) -> QuerySet:
        """Returns all rows in the table"""
        query = "SELECT * FROM {0};".format(self.model.table_name)
        return QuerySet(
            self.model, [self._return_model(row) for row in await self.db.fetch(query)]
        )

    async def get(self, id=None, **kwargs):
        """Returns a single row with the given values"""
        self.model(**kwargs)
        if id:
            query = "SELECT * FROM {0} WHERE Id=$1;".format(self.model.table_name)
            return self._return_model(await self.db.fetchrow(query, id))
        else:
            count = 1
            params = []
            for key in kwargs.keys():
                params.append(f"{key}=${count}")
                count += 1
            query = "SELECT * FROM {0} WHERE {1};".format(
                self.model.table_name, " AND ".join(params)
            )
            return self._return_model(
                await self.db.fetchrow(query, *tuple(kwargs.values()))
            )

    async def filter(self, **kwargs):
        """Similar to get but returns multiple rows if exists"""
        self.model(**kwargs)
        count = 1
        params = []
        for key in kwargs.keys():
            params.append(f"{key}=${count}")
            count += 1
        query = "SELECT * FROM {0} WHERE {1};".format(
            self.model.table_name, " AND ".join(params)
        )
        return QuerySet(
            self.model,
            [
                self._return_model(row)
                for row in await self.db.fetch(query, *tuple(kwargs.values()))
            ],
        )

    async def search(self, **kwargs) -> QuerySet:
        """Runs a SQL search query with the given values"""
        self.model(**kwargs)
        count = 1
        params = []
        for key in kwargs.keys():
            params.append(f"{key} LIKE '%' || ${count} || '%'")
            count += 1
        query = "SELECT * FROM {0} WHERE {1};".format(
            self.model.table_name, " AND ".join(params)
        )

        return QuerySet(
            self.model,
            [
                self._return_model(row)
                for row in await self.db.fetch(query, *tuple(kwargs.values()))
            ],
        )

    async def create(self, **kwargs):
        """
        Creates and returns new model instance with the given values and saves it in the database
        """
        self.model(**kwargs)
        table_name = self.model.table_name
        col_string = ", ".join(kwargs.keys())
        params = []
        count = 1
        for i in range(len(kwargs.keys())):
            params.append(f"${count}")
            count += 1
        param_string = ", ".join(params)

        values = []
        for v in kwargs.values():
            if isinstance(v, models.base_model.Model):
                values.append(v.id)
            else:
                values.append(v)

        for field in self.model.fields:
            for validator in field.data_validators:
                for key, value in kwargs.items():
                    if field.column_name == key:
                        validator(value)

        query = f"INSERT INTO {table_name} ({col_string}) VALUES({param_string}) RETURNING Id;"

        instance_id = await self.db.fetchval(query, *tuple(kwargs.values()))
        kwargs["id"] = instance_id
        return self.model(**kwargs)
