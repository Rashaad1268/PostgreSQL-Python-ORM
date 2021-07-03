```python
from pg_orm import models
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

pg_pool.closeall() # Close the pool at last
```
Congratulations you have created a Model, as simple as that  
Refer to `rows.md` if you want to know about handling rows