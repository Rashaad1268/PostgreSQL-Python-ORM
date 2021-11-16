# Brief documentation about the library

This documentation will get replaced by actual documentation

----

## `class pg_orm.models.Model`

The base class of models

### `save(commit=True)`

Saves the current model istance to the database

### `delete(commit=True)`

Deletes the current instace from the database

### `update(commit=True)`

Updates the model insatace in the database to the current instance

### `__eq__(other)`

Compares to model objects by the class and the id

### `__hash__()`

Returns the hash of the models id

## `class pg_orm.models.AsyncModel`

Same as model but the following methods are async and should be `await`ed

- `save`
- `delete`
- `update`

## `class pg_orm.models.manager.Manager(model)`

The default manager of a [`pg_orm.models.Model`](#class-pg_orm.models.model).
The manager is responsible for querying the table.

The manager can be access through `Model.objects`

### `all() -> QuerySet`

Returns all the rows in the table

### `get(id=None, **kwargs) -> Model`

Returns a single row from the table with the given arguments

### `filter(**kwargs) -> QuerySet`

Returns multiple rows from the from with the given arguments

### `search(**kwargs) -> QuerySet`

Runs a SQL search query and returns the rows which match the given arguments

### `create(**kwargs) -> Model`

Creates a new row with the given arguments and returns a model instance of it

## `class pg_orm.models.manager.AsyncManager(model)`

Same as [`Manager`](#class-pg_orm.models.manager.manager) but the following methods are async and should be `await`ed

- `all`
- `get`
- `filter`
- `search`
- `create`
