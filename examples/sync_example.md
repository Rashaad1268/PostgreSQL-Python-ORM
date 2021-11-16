```python
# models.py file
from pg_orm import models, migrate
from psycopg2 import pool

uri = "postgresql://user:password_1234@127.0.0.1:5432/postgres"
pg_pool = pool.SimpleConnectionPool(1, 10, uri)
Model = models.create_model(pg_pool)

class Post(Model):
    # We are making a post model
    # An id field will be automatically set by the library
    title = models.CharField(max_length=255)
    body = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True) # Now the date_created will be automatically set

migrate(Post)

pg_pool.closeall() # Close the pool at last
```

Check [`migrations.md`](https://github.com/Rashaad1268/PostgreSQL-Python-ORM/blob/main/examples/migrations.md)
on applying the migrations
and [`rows.md`](https://github.com/Rashaad1268/PostgreSQL-Python-ORM/blob/main/examples/rows.md)
on querying the database
