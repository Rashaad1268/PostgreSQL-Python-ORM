import datetime
import logging
import inspect
from typing import Optional, Any, Callable, Union

from pg_orm.errors import SchemaError
from pg_orm.models.utils import PythonToSQLConverter as PyToSQL

log = logging.getLogger(__name__)


class Empty:
    pass


class Field:
    python = None  # The field data type in python

    def __init__(
        self,
        null: bool = False,
        unique: bool = False,
        default: Any = None,
        default_insertion_value: Optional[Callable] = None,
        validators: Union[list[Callable], tuple[Callable]] = [],
    ):
        self.column_name = None
        self.data_validators = validators
        self.is_unique = unique
        self.primary_key = False
        self.nullable = null  # Fields aren't nullable by default
        self.default = default
        self.default_insertion_value = default_insertion_value

    def __copy__(self):
        new = Empty()
        new.__class__ = self.__class__
        new.__dict__ = self.__dict__.copy()
        return new

    def __eq__(self, other):
        return isinstance(self, other) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        path = "%s.%s" % (self.__class__.__module__, self.__class__.__qualname__)
        return "<%s>" % path

    def to_sql(self):
        raise NotImplementedError()

    def _get_default_val(self):
        if self.default is not None:
            de = self.default
            if inspect.ismethod(de) or inspect.isfunction(de) or inspect.isbuiltin(de):
                return f" DEFAULT {PyToSQL.convert(de())}"
            else:
                return f" DEFAULT {PyToSQL.convert(de)}"
        return ""

    def is_real_type(self):
        """To check if the field is a real data type"""
        return True


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

        if auto_increment:
            self.python = None

        if small_int and big_int:
            raise SchemaError("Integer column cannot be big and small.")

    def to_sql(self):
        null = ""
        unique = ""
        pg_type = "INTEGER"
        if not self.nullable:
            null = " NOT NULL"
        if self.is_unique:
            unique = " UNIQUE"

        if self.auto_increment:
            if self.big_int:
                pg_type = "BIGSERIAL"
            elif self.small_int:
                pg_type = "SMALLSERIAL"
            pg_type = "SERIAL"
        if self.big_int:
            pg_type = "BIGINT"
        elif self.small_int:
            pg_type = "SMALLINT"

        return f"{pg_type}{unique}{null}{self._get_default_val()}"

    def is_real_type(self):
        return not self.auto_increment


class AutoIncrementIDField(IntegerField):
    """An auto increasing id field, used as the id row for models"""

    python = None

    def __init__(self, small_int: bool = False, big_int: bool = False, null=True):
        super().__init__(
            big_int=big_int,
            small_int=small_int,
            auto_increment=True,
            null=null,
            unique=True,
        )

    def is_real_type(self):
        return False


class CharField(Field):
    """A field for strings, for small to large sized strings.
    For large amounts of text, use TextField."""

    python = str

    def __init__(self, max_length: int = None, **kwargs):
        self.max_length = max_length
        super().__init__(**kwargs)

    def to_sql(self):
        null = ""
        unique = ""
        pg_type = f"VARCHAR({self.max_length})"
        if not self.nullable:
            null = " NOT NULL"
        if self.is_unique:
            unique = " UNIQUE"
        if not self.max_length:
            pg_type = "TEXT"

        return f"{pg_type}{unique}{null}{self._get_default_val()}"


class FloatField(IntegerField):
    """A field for boolean values"""

    python = float

    def to_sql(self):
        null = ""
        unique = ""
        if not self.nullable:
            null = " NOT NULL"
        if self.is_unique:
            unique = " UNIQUE"

        return f"REAL{unique}{null}{self._get_default_val()}"


class TextField(CharField):
    """A field for large string based values"""

    python = str

    def __init__(self, max_length=None, **kwargs):
        kwargs["max_length"] = max_length
        super().__init__(**kwargs)


class DateTimeField(Field):
    """A field for datetime values"""

    python = datetime.datetime

    def __init__(
        self, auto_now_add: bool = False, has_timezone: bool = False, **kwargs
    ):
        self.automatically_add = auto_now_add
        self.has_timezone = has_timezone
        super().__init__(**kwargs)

    def _get_default_val(self):
        default = ""
        if self.automatically_add:
            default = self.default or (
                " DEFAULT current_timestamp" if self.automatically_add else ""
            )
            return default
        elif self.default:
            default = self.default or (
                " DEFAULT current_timestamp" if self.automatically_add else ""
            )
        return default

    def to_sql(self):
        null = ""
        unique = ""

        pg_type = "TIMESTAMP"
        if not self.nullable:
            null = " NOT NULL"
        if self.is_unique:
            unique = " UNIQUE"

        if self.has_timezone:
            pg_type = "TIMESTAMP WITH TIMEZONE"

        return f"{pg_type}{unique}{null}{self._get_default_val()}"


class BooleanField(Field):
    """A field to store boolean values"""

    python = bool

    def to_sql(self):
        null = " NOT NULL"
        unique = ""

        if self.nullable:
            null = " NULL"
        if self.is_unique:
            unique = " UNIQUE"
        return f"BOOL{unique}{null}{self._get_default_val()}"


class ForeignKey(Field):
    def __init__(
        self, to, on_delete: str, sql_type: Optional[str] = "INTEGER", column: str="Id", **kwargs
    ):
        super().__init__(**kwargs)

        options = (
            "NO ACTION",
            "RESTRICT",
            "CASCADE",
            "SET NULL",
            "SET DEFAULT",
        )
        if on_delete.upper() not in options:
            raise SchemaError("Invalid action passed in on_delete")

        self.to = to
        self.sql_type = sql_type
        self.column = column
        self.on_delete = on_delete.upper()

    def to_sql(self):
        sql = "{0.sql_type} REFERENCES {0.to.table_name}({0.column}) " "ON DELETE {0.on_delete}"
        return sql.format(self)

    def is_real_type(self):
        return False


class JsonField(Field):
    python = dict

    def to_sql(self):
        null = ""
        unique = ""
        if not self.nullable:
            null = " NOT NULL"
        if self.is_unique:
            unique = " UNIQUE"

        return f"JSON {unique}{null}{self._get_default_val()}"



class BinaryField(Field):
    python = bytes

    def to_sql(self):
        null = ""
        unique = ""
        if not self.nullable:
            null = " NOT NULL"
        if self.is_unique:
            unique = " UNIQUE"

        return f"BYTEA {unique}{null}{self._get_default_val()}"
