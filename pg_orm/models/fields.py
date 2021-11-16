import datetime
import logging
import inspect
import pydoc
from typing import Optional, Any, Callable, Union

from pg_orm.validators import Validator
from pg_orm.errors import SchemaError
from pg_orm.models import base_model
from pg_orm.models.utils import PythonToSQLConverter as PyToSQL

log = logging.getLogger(__name__)


class Field:
    python = None  # The field data type in python

    def __init__(
        self,
        null: bool = False,
        unique: bool = False,
        default: Any = None,
        primary_key: bool = None,
        default_insertion_value: Optional[Callable] = None,
        validators: Union[list[Callable], tuple[Callable]] = [],
    ):
        self.column_name = None # This will be replaced later
        self.validators = validators
        self.is_unique = unique
        self.primary_key = primary_key
        self.nullable = null  # Fields aren't nullable by default
        self.default = default
        self.default_insertion_value = default_insertion_value

    def to_dict(self):
        data = self.__dict__.copy()
        cls = self.__class__
        data["__meta__"] = cls.__module__ + "." + cls.__qualname__

        return data

    @classmethod
    def from_dict(cls, data):
        meta = data["__meta__"]
        given = cls.__module__ + "." + cls.__qualname__

        if given != meta:
            cls = pydoc.locate(meta)
            if cls is None:
                raise RuntimeError('Could not locate "%s".' % meta)

        self = cls.__new__(cls)
        self.__dict__.update(data)
        return self

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

    def _get_null_val(self):
        if self.nullable:
            return " NULL"
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

        if small_int and big_int:
            raise SchemaError("Integer column cannot be big and small.")

        if auto_increment:
            self.python = None

    def to_sql(self):
        pg_type = "INTEGER"
        if self.auto_increment:
            if self.big_int:
                pg_type = "BIGSERIAL"
            elif self.small_int:
                pg_type = "SMALLSERIAL"
            else:
                pg_type = "SERIAL"
        elif self.big_int:
            pg_type = "BIGINT"
        elif self.small_int:
            pg_type = "SMALLINT"

        return f"{pg_type}{self._get_pk_val()}{self._get_unique_val()}{self._get_null_val()}{self._get_default_val()}"

    def is_real_type(self):
        return not self.auto_increment


class AutoIncrementIDField(IntegerField):
    """An auto increasing id field, used as the id row for models"""

    python = None

    def __init__(self, small_int: bool = False, big_int: bool = False):
        super().__init__(
            big_int=big_int, small_int=small_int, auto_increment=True, primary_key=True
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
        pg_type = f"VARCHAR({self.max_length})" if self.max_length is not None else "TEXT"
        return f"{pg_type}{self._get_pk_val()}{self._get_unique_val()}{self._get_null_val()}{self._get_default_val()}"


class FloatField(IntegerField):
    """A field for boolean values"""

    python = float

    def to_sql(self):  
        pg_type = "REAL"
        return f"{pg_type}{self._get_pk_val()}{self._get_unique_val()}{self._get_null_val()}{self._get_default_val()}"


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
        self, auto_now_add: bool = False, timezone: str = False, **kwargs
    ):
        self.automatically_add = auto_now_add
        self.timezone = timezone
        super().__init__(**kwargs)

    def _get_default_val(self):
        default = ""
        if self.automatically_add:
            default = " CURRENT_TIMESTAMP"
            if self.timezone is not None:
                default = f" DEFAULT (NOW() AT TIME ZONE '{self.timezone}')"
            return default

        else:
            default = super()._get_default_val()
            return default

        return default

    def to_sql(self):
        pg_type = "TIMESTAMP WITH TIME ZONE" if self.timezone is not None else "TIMESTAMP"
        return f"{pg_type}{self._get_pk_val()}{self._get_unique_val()}{self._get_null_val()}{self._get_default_val()}"


class BooleanField(Field):
    """A field to store boolean values"""

    python = bool

    def to_sql(self):
        pg_type = "BOOL"
        return f"{pg_type}{self._get_pk_val()}{self._get_unique_val()}{self._get_null_val()}{self._get_default_val()}"


class ForeignKey(Field):
    def __init__(
        self,
        to,
        on_delete: str,
        sql_type: Optional[str] = "INTEGER",
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

        if isinstance(to, base_model.ModelBase):
            self.to = to.table_name

        elif isinstance(to, str):
            self.to = to

        if isinstance(column, Field):
            self.column = column.column_name
        elif isinstance(column, str):
            self.column = column

        self.sql_type = sql_type
        self.on_delete = on_delete.upper()

    def to_sql(self):
        sql = "{0.sql_type} REFERENCES {0.to}({0.column}) " "ON DELETE {0.on_delete}"
        return sql.format(self)

    def is_real_type(self):
        return False


class JsonField(Field):
    python = dict

    def to_sql(self):
        return f"JSON{self._get_pk_val()}{self._get_unique_val()}{self._get_null_val()}{self._get_default_val()}"


class BinaryField(Field):
    python = bytes

    def to_sql(self):
        null = ""
        unique = ""
        if not self.nullable:
            null = " NOT NULL"
        if self.is_unique:
            unique = " UNIQUE"

        return f"BYTEA{self._get_pk_val()}{self._get_unique_val()}{self._get_null_val()}{self._get_default_val()}"


class ArrayField(Field):
    def __init__(self, sql_type: str, **kwargs):
        self.sql_type = sql_type
        super().__init__(**kwargs)
    
    def to_sql(self):
        return "{0.sql_type} ARRAY".format(self)

class DateField(Field):
    pass


class TimeDeltaField(Field):
    pass
