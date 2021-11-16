# Applying migrations

Applying the migrations will apply any changes in your code to the database.

----

> It is recommended to create a new file named `migrations.py`

If you are using `pg_orm.models.Model`

```python
# migrations.py
from pg_orm.migrations.migration import migrate

migrate(Post)  # Pass in the model class
```

The above method can be used to apply migrations for a single model.

If you want to apply migrations to all of your models

```python
# migrations.py
from pg_orm import migrate

migrate_all()  # This will apply migrations for all of your models which subclass this class
```

If you are using `pg_orm.models.AsyncModel`

```python
# migrations.py
from pg_orm import async_migrate
from asyncio import get_event_loop

# async_migrate is a coroutine
get_event_loop().run_until_complete(async_migrate(Post))  # Pass in the model class
```

If you want to apply migrations to all of the models use `pg_orm.async_migrate_all`
