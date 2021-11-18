from .base_model import Model, AsyncModel
from .fields import *

CASCADE = "CASCADE"
NO_ACTION = "NO ACTION"
RESTRICT = "RESTRICT"
SET_NULL = "SET NULL"
SET_DEFAULT = "SET DEFAULT"


class SQLTypes:
    integer = "INTEGER"
    big_int = "BIGINT"
    small_int = "SMALLINT"
    text = "TEXT"
    varchar = lambda max_len: f"VARCHAR({max_len})"
    boolean = "BOOL"
    time_delta = "INTERVAL"
    date = "DATE"
    date_time = lambda has_tz=False: "TIMESTAMP WITH TIME ZONE" if has_tz else "TIMESTAMP"
