## PostgreSQL Python ORM (pg_orm)
_____
Tired by executing raw SQL?  
Fear no more because **pg_orm** is here!
_____
This package is not on pypi you have to download it from github
>  `pip install git+https://github.com/Rashaad1268/PostgreSQL-Python-ORM.git#egg=pg_orm`
____
**Features:**
- Ability to interact with PostgreSQL databases using python
- Create tables, create/delete/get rows with ease
- Asynchronous support  

And much more!  
____
Example synchronous usage:
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
For the migrations you need to make a new file called `migrations.py`
```python
# migrations.py
from pg_orm import migrations
from psycopg2 import pool

pg_pool = pool.SimpleConnectionPool(**data)
migrations.apply_migrations(pg_pool)
```
And that's it!.  
Now for getting/saving/deleting data from the database
```python
# We will be using the post model which you created earlier

# Lets create some rows
for i in range(5):
    post = Post(title=f"Test Post {i}", body=f"This is a Test Post {i}") # The date_created will be automatically set
    post.save() # Save the post
# The above code will create 5 rows in the database

# Now we will get the rows in the database
first_post = Post.objects.get(id=1) # Returns the row where the id is 1
print(first_post.body)
#  Output: This is a Test Post 1

# Lets get some rows by other attributes
post = Post.objects.get(title=f"Test Post 3")
print(post.body)
#  Output: This is a Test Post 3

# Now lets delete some rows
# We already have the Post object
post.delete() # Deletes the row from the database
```
Note:  
`Model.objects.get()` only returns one row
If you want multiple rows use `Model.objects.filter()` instead
