class DBError(Exception):
    """Main exception class"""

    pass


class SchemaError(DBError):
    pass


class FiledError(DBError):
    def __init__(self, key, options):
        self.key = key
        self.options = options
        super().__init__(
            f"Cannot resolve keyword '{key}' into field. "
            f"Choices are: {', '.join(self.options)}"
        )


class ValidationError(DBError):
    """Error raised when a data validator failed."""
    pass


class DataBaseNotConfigured(DBError):
    """Raised when the database is not properly configured"""

    def __init__(self):
        super().__init__("DataBase is not properly configured."
                         "\nUse pg_orm.init_db and configure the database properly.")
