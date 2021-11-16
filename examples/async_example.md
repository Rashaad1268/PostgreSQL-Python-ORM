```python
# models.py file
import asyncpg
import asyncio

from pg_orm import models, async_migrate

run = asyncio.get_event_loop().run_until_complete

uri = "postgresql://user:password_1234@127.0.0.1:5432/postgres"
pg_pool = run(asyncpg.create_pool(uri))
Model = models.create_async_model(pg_pool)

class Post(Model):
    # We are making a post model
    # An id field will be automatically set by the library
    title = models.CharField(max_length=255)
    body = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True) # Now the date_created will be automatically set

run(async_migrate(Post))

run(pg_pool.close()) # Close the pool at last
```

Congratulations you have created a Model!  

Check [`migrations.md`](https://github.com/Rashaad1268/PostgreSQL-Python-ORM/blob/main/examples/migrations.md)
on applying the migrations
and [`rows.md`](https://github.com/Rashaad1268/PostgreSQL-Python-ORM/blob/main/examples/rows.md)
on querying the database
