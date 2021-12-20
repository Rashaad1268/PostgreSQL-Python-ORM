import datetime
import pydoc
from typing import Iterable, Any, Callable, Optional

from pg_orm.errors import SchemaError
from pg_orm.models import base_model
from pg_orm.models.utils import maybe_await
from pg_orm.models.utils import quote


class Field:
    python = None  # The field data type in python
    postgresql = None  # The value will be set in the subclasses

    def __init__(
            self,
            null: bool = False,
            unique: bool = False,
            primary_key: bool = None,
            default: Any = None,
            default_sql_value: Any = None,
            validators: Optional[Iterable[Callable[[Any], Any]]] = None,
    ):
        self.column_name = None  # This will be replaced later
        self.validators = validators
        self.is_unique = unique
        self.primary_key = primary_key
        self.nullable = null  # Fields aren't nullable by default
        self.default = default
        self.default_sql_value = default_sql_value

        if validators is None:
            self.validators = []

    def to_dict(self):
        data = self.__dict__.copy()
        data.pop("default", None)
        cls = self.__class__
        data["path"] = cls.__module__ + "." + cls.__qualname__

        return data

    @classmethod
    def from_dict(cls, data):
        meta = data["path"]
        given = cls.__module__ + "." + cls.__qualname__

        if given != meta:
            cls = pydoc.locate(meta)
            if cls is None:
                raise RuntimeError('Could not locate "%s".' % meta)

        self = cls.__new__(cls)
        self.__dict__.update(data)
        return self

    def to_sql(self):
        if self.postgresql is None:
            raise NotImplementedError()
        return f"{self.postgresql}{self._get_pk_val()}{self._get_unique_val()}"\
                f"{self._get_null_val()}{self._get_default_sql_val()}"

    def _get_default_python_val(self):
        if callable(self.default):
            return maybe_await(self.default)
        else:
            return self.default

    def _get_default_sql_val(self):
        if self.default_sql_value:
            if callable(self.default_sql_value):
                return f" DEFAULT {quote(maybe_await(self.default_sql_value))}"
            else:
                return f" DEFAULT {quote(self.default_sql_value)}"
        else:
            return ""

    def _get_null_val(self):
        if self.nullable:
            return ""
        elif not self.nullable:
            return " NOT NULL"

    def _get_pk_val(self):
        if self.primary_key:
            return " PRIMARY KEY"
        else:
            return ""

    def _get_unique_val(self):
        if self.is_unique:
            return " UNIQUE"
        else:
            return ""

    def __copy__(self):
        cls = self.__class__
        new = cls.__new__(cls)
        new.__dict__.update(self.__dict__)
        return new

    def __eq__(self, other):
        return isinstance(self, Field) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        path = "%s.%s" % (self.__class__.__module__, self.__class__.__qualname__)
        return "<%s>" % path


class IntegerField(Field):
    """Field to store integers"""

    python = int

    def __init__(
            self,
            small_int: bool = False,
            big_int: bool = False,
            auto_increment: bool = False,
            **kwargs,
    ):
        self.small_int = small_int
        self.big_int = big_int
        self.auto_increment = auto_increment
        super().__init__(**kwargs)

        if small_int and big_int:
            raise SchemaError("Integer column cannot be big and small.")

        if auto_increment:
            self.python = None

        postgresql = "INTEGER"
        if self.auto_increment:
            if self.big_int:
                postgresql = "BIGSERIAL"
            elif self.small_int:
                postgresql = "SMALLSERIAL"
            else:
                postgresql = "SERIAL"
        elif self.big_int:
            postgresql = "BIGINT"
        elif self.small_int:
            postgresql = "SMALLINT"

        self.postgresql = postgresql


class AutoIncrementIntegerField(IntegerField):
    """An automatically increasing integer field"""

    python = None

    def __init__(self, small_int: bool = False, big_int: bool = False):
        super().__init__(
            big_int=big_int, small_int=small_int, auto_increment=True, primary_key=True
        )


class CharField(Field):
    """A field for strings, for small to large sized strings.
    For large amounts of text, use TextField."""

    python = str

    def __init__(self, max_length: int = None, **kwargs):
        self.max_length = max_length
        super().__init__(**kwargs)
        self.postgresql = f"VARCHAR({self.max_length})" if self.max_length is not None else "TEXT"


class FloatField(IntegerField):
    """A field for boolean values"""

    python = float
    postgresql = "REAL"


class TextField(CharField):
    """A field for large string based values"""

    def __init__(self, max_length=None, **kwargs):
        kwargs["max_length"] = max_length
        super().__init__(**kwargs)


class DateTimeField(Field):
    """A field for datetime values"""

    python = datetime.datetime

    def __init__(self, has_timezone=False, **kwargs):
        self.has_timezone = has_timezone
        super().__init__(**kwargs)
        self.postgresql = "TIMESTAMP WITH TIME ZONE" if self.has_timezone is not None else "TIMESTAMP"


class BooleanField(Field):
    """A field to store boolean values"""

    python = bool
    postgresql = "BOOL"


class ForeignKey(Field):
    def __init__(
            self,
            to,
            on_delete: str,
            sql_type: str,
            column: str = "Id",
            **kwargs,
    ):
        options = (
            "NO ACTION",
            "RESTRICT",
            "CASCADE",
            "SET NULL",
            "SET DEFAULT",
        )
        if on_delete.upper() not in options:
            raise SchemaError("Invalid action passed in on_delete")

        super().__init__(**kwargs)

        if isinstance(to, base_model.BaseModel):
            self.to = to.table_name

        elif isinstance(to, str):
            self.to = to

        if isinstance(column, Field):
            self.column = column.column_name
        elif isinstance(column, str):
            self.column = column

        self.sql_type = sql_type
        self.on_delete = on_delete.upper()
        self.postgresql = "{0.sql_type} REFERENCES {0.to}({0.column}) ON DELETE {0.on_delete}".format(self)


class JsonField(Field):
    python = dict
    postgresql = "JSON"


class BinaryField(Field):
    python = bytes
    postgresql = "BYTEA"


class ArrayField(Field):
    python = list

    def __init__(self, sql_type: str, **kwargs):
        self.sql_type = sql_type
        super().__init__(**kwargs)
        self.postgresql = f"{self.sql_type} ARRAY"


class DateField(Field):
    python = datetime.date

    def __init__(self):
        raise NotImplementedError


class TimeDeltaField(Field):
    python = datetime.timedelta

    def __init__(self):
        raise NotImplementedError
