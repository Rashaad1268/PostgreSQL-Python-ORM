## Just some brief documentation about the library
This documentation will get replaced by actual documentation

`Model.create_table` - Creates a table for the model if it doesn't exist already

`Model.save` - Saves the current model istance to the database

`Model.delete` - Deletes the current model instace from the database

`Model.update` - Updates the model insatace in the database to the current instance

`Model.__eq__` - Compares to model objects by the class and the id

`Model.__hash__` - Returns the hash of the models id

`Model.objects.all` - Returns all the rows in the database

`Model.objects.get` - Returns a single row from the database with the given attributes

`Model.objects.filter` - Returns multiple rows from the database with the given attributes

`Model.objects.search` - Run a SQL search query and returns the rows which match the query

`Model.objects.create` - Creates a new row in the database with the given attributes and returns a model instance of it
