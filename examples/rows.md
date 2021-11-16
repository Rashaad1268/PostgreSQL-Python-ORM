## Getting/saving/editing/deleting data from the database

```python
# We will be using the post model which we created earlier

# Lets create some rows
for i in range(5):
    post = Post(title=f"Test Post {i}", body=f"This is a Test Post {i}") # The date_created will be automatically set
    post.save() # Save the post
# The above code will create 5 rows in the database

# Now we will get the rows in the database
first_post = Post.objects.get(id=1) # Returns the row where the id is 1
# The id parameter can also be passed in positionally
print(first_post.body)
#  Output: This is a Test Post 1

# Lets get some rows by other attributes
post = Post.objects.get(title=f"Test Post 3")
print(post.body)
#  Output: This is a Test Post 3

# Now lets delete some rows
# We already have the Post object
post.delete() # Deletes the row from the database

# Now lets edit the attributes of a post
# We have the instance of the first post already so we'll use that
first_post.title = "The title of this post is edited"

# Now let's update the post in the database
first_post.update()
```
