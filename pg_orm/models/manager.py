from pg_orm import models
from pg_orm.models.queryset import QuerySet
from pg_orm.models.utils import maybe_await


class Manager:
    def __init__(self, model):
        self.model = model
        self.db = getattr(model, "db", None)

    def all(self) -> QuerySet:
        """Returns all rows in the table"""
        query = "SELECT * FROM {0};".format(self.model.table_name)
        return QuerySet(
            self.model, [self._return_model(row) for row in self.db.fetchall(query)]
        )

    def get(self, **kwargs):
        """Returns a single row with the given values"""
        self.model(**kwargs)
        query, args = self.model._query_gen.generate_select_query(**kwargs)
        r = self.db.fetchone(query, *args)
        return self._return_model(r)

    def filter(self, **kwargs) -> QuerySet:
        """Similar to get but returns multiple rows if exists"""
        self.model(**kwargs)
        query, args = self.model._query_gen.generate_select_query(**kwargs)

        return QuerySet(
            self.model,
            [
                self._return_model(row)
                for row in self.db.fetchall(query, *args)
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

        for key, value in kwargs.items():
            for validator in self.model.fields[key].validators:
                maybe_await(validator(value))

        all_fields = set(self.model.fields)
        all_fields.discard("id")
        unspecified_fields = set(all_fields) - set(kwargs)
        for field_name in unspecified_fields:
            field = self.model.fields[field_name]
            if field.default is not None:
                kwargs[field_name] = field._get_default_python_val()

        query, values = self.model._query_gen.generate_insert_query(True, **kwargs)
        new_instance_data = self.db.fetchone(query, *values, commit=True)

        return self.model(**new_instance_data)

    def _return_model(self, query_set: dict):
        if bool(query_set):
            return self.model(**query_set)
        else:
            return None


class AsyncManager(Manager):
    async def all(self) -> QuerySet:
        """Returns all rows in the table"""
        query = "SELECT * FROM {0};".format(self.model.table_name)
        return QuerySet(
            self.model, [self._return_model(row) for row in await self.db.fetch(query)]
        )

    async def get(self, **kwargs):
        """Returns a single row with the given values"""
        self.model(**kwargs)
        query, args = self.model._query_gen.generate_select_query(True, **kwargs)
        return self._return_model(
            await self.db.fetchrow(query, *args)
        )

    async def filter(self, **kwargs):
        """Similar to get but returns multiple rows if exists"""
        self.model(**kwargs)
        query, args = self.model._query_gen.generate_select_query(True, **kwargs)
        return QuerySet(
            self.model,
            [
                self._return_model(row)
                for row in await self.db.fetch(query, *args)
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
            ]
          )

    async def create(self, **kwargs):
        """
        Creates and returns new model instance with the given values and saves it in the database
        """
        self.model(**kwargs)

        for key, value in kwargs.items():
            for validator in self.model.fields[key].validators:
                maybe_await(validator(value))

        all_fields = set(self.model.fields)
        all_fields.discard("id")
        unspecified_fields = set(all_fields) - set(kwargs)
        for field_name in unspecified_fields:
            field = self.model.fields[field_name]
            if field.default is not None:
                kwargs[field_name] = field._get_default_python_val()

        query, values = self.model._query_gen.generate_insert_query(True, asyncpg=True, **kwargs)
        new_instance_data = await self.db.fetchrow(query, *values)

        return self.model(**new_instance_data)
