For the migrations you need to make a new file called `migrations.py`
```python
# migrations.py
from pg_orm import migrations
from psycopg2 import pool

from models import Model # The Model variable in the models file which you create your models in

pg_pool = pool.SimpleConnectionPool(**data)
migrations.apply_migrations(pg_pool)
```
Or you can use Model.create_table to create the table for the model 
```python
with pg_pool.getconn() as conn:
    Post.create_table(conn)
    pg_pool.putconn(conn)
```
