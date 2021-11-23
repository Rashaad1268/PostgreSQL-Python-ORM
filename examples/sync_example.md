```python
# models.py file
import pg_orm
from pg_orm import models, migrations
from psycopg2 import pool

URI = "postgresql://user:password_1234@127.0.0.1:5432/postgres"
pg_pool = pool.SimpleConnectionPool(1, 10, URI)
pg_orm.init_db(psycopg2_pool=pg_pool)

class Post(models.Model, table_name="Post"):
    # We are making a post model
    # An id field will be automatically set by the library
    # If one is not already set
    title = models.CharField(max_length=255)
    body = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True) # Now the date_created will be automatically set

migrations.migrate_all()

pg_pool.closeall() # Close the pool at last
```

Check [`migrations.md`](https://github.com/Rashaad1268/PostgreSQL-Python-ORM/blob/main/examples/migrations.md)
on applying the migrations
and [`rows.md`](https://github.com/Rashaad1268/PostgreSQL-Python-ORM/blob/main/examples/rows.md)
on querying the database
