from itertools import zip_longest
from typing import Iterable, Tuple, List, Union

from pg_orm.models.utils import quote, QueryParamStyle


class Component:
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"
    POW = "^"

    EQ = "="
    LT = "<"
    GT = ">"
    LE = "<="
    GE = ">="
    NE = "!="

    LOGICAL_AND = " AND "
    LOGICAL_OR = " OR "

    BIT_AND = "&"
    BIT_OR = "|"
    XOR = "^"

    def as_sql(self, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement as_sql()")

    def to_sql(self, vendor: str = None, *args, **kwargs) -> Union[Tuple[str, Iterable[str]], str]:
        """Returns the as_{vendor} method if exists else returns as_sql() method"""
        if vendor is None:
            return self.as_sql(*args, **kwargs)

        return getattr(self, f"as_{vendor}", self.as_sql)(*args, **kwargs)

    @staticmethod
    def _components_to_sql(components: "Union[Iterable[Component], Iterable[str], Component, str]", vendor: str = None,
                           return_str: bool = True) -> List[str]:

        if isinstance(components, str):
            if return_str:
                return [components]
            else:
                raise TypeError("Got string and expected Component or list of Components")

        if isinstance(components, Component):
            return [components.to_sql()]

        sql = []
        for component in components:
            if isinstance(component, Component):
                sql.append(component.to_sql(vendor))
            else:
                sql.append(component)
        return sql

    @staticmethod
    def _cast_queryparams(query_params: "Iterable[QueryParam]", vendor: str = None, add_name: bool = True):
        return [query_param.to_sql(vendor) for query_param in query_params]


class Column(Component):
    def __init__(self, name: str, table_name: str = None):
        self.name = name
        self.condition = ""

        if table_name:
            self.name = table_name + "." + name

    def _combine(self, operator_string: str, other) -> "Value":
        if isinstance(other, Column):
            condition = self.name + operator_string + other.name
        elif isinstance(other, Value):
            condition = self.condition = self.name + operator_string + other.value

        else:
            condition = self.name + operator_string + str(quote(other))

        if not self.condition:
            self.condition = condition

        return Value(condition)

    def __eq__(self, other) -> "Value":
        return self._combine(self.EQ, other)

    def __ne__(self, other) -> "Value":
        return self._combine(self.NE, other)

    def __add__(self, other) -> "Value":
        return self._combine(self.ADD, other)

    def __sub__(self, other) -> "Value":
        return self._combine(self.SUB, other)

    def __truediv__(self, other) -> "Value":
        return self._combine(self.DIV, other)

    def __floordiv__(self, other) -> "Value":
        return self._combine(self.DIV, other)

    def __ror__(self, other) -> "Value":
        return self._combine(self.LOGICAL_OR, other)

    def __rand__(self, other) -> "Value":
        return self._combine(self.LOGICAL_AND, other)

    def __xor__(self, other) -> "Value":
        return self._combine(self.XOR, other)

    def __lt__(self, other) -> "Value":
        return self._combine(self.LT, other)

    def __gt__(self, other) -> "Value":
        return self._combine(self.GT, other)

    def __ge__(self, other) -> "Value":
        return self._combine(self.GE, other)

    def __le__(self, other) -> "Value":
        return self._combine(self.LE, other)

    def __and__(self, other) -> "Value":
        return self._combine(self.BIT_AND, other)

    def __or__(self, other) -> "Value":
        return self._combine(self.BIT_OR, other)

    def as_sql(self):
        if self.condition:
            return self.condition
        return self.name


class Where(Component):
    def __init__(self, conditions, default_condition_join: str = " AND ", conditions_join: List[str] = None):
        self.conditions = self._components_to_sql(conditions)
        self.conditions_join = conditions_join  # The sql operator to join the conditions
        self.default_condition_join = default_condition_join

        if conditions_join and len(conditions_join) != len(self.conditions) - 1:
            raise ValueError("The length of conditions_join needs to be one item less than conditions")

        if default_condition_join and not conditions_join:
            self.conditions_join = [default_condition_join for _ in range(len(self.conditions) - 1)]

    def as_sql(self):

        sql = "WHERE "

        conditions = self._components_to_sql(self.conditions)
        result = []
        for cond, condition_join in zip_longest(conditions, self.conditions_join):
            result.append(cond)
            if condition_join is not None:
                result.append(condition_join)
        sql += "".join(result)

        return sql


class OrderBy(Component):
    def __init__(self, columns: Iterable[str], sequences=None):
        self.columns = columns
        self.sequences = sequences

        if sequences is None:
            self.sequences = [True for _ in columns]

    def as_sql(self):
        sql = f"ORDER BY "
        sql += ",\n".join(f"{col_name} {sequence}"
                          for col_name, sequence in
                          zip(self.columns, self.sequences))

        return sql


class Star(Component):
    def as_sql(self):
        return "*"


class Join(Component):
    def __init__(self, table_name: str, on: Union[str, Iterable[str]], join_type: str = "INNER"):
        self.table_name = table_name
        self.join_type = join_type
        self.on = on

    def as_sql(self):
        sql = f"{self.join_type} JOIN {self.table_name}"

        on = self.on if isinstance(self.on, str) else ",\n".join(self.on)

        if on:
            sql += " ON " + on

        return sql


class Select(Component):
    def __init__(self, table: str = None, columns: Union[Iterable[Component], Iterable[str], Component, str] = None,
                 join: Join = None,
                 where: Where = None, limit: int = None, expression: str = None):
        self.expression = expression
        self.table = table
        self.where = where
        self.limit = limit
        self.join = join
        self.columns = columns

    def as_sql(self):
        sql = "SELECT "
        columns = self._components_to_sql(self.columns)
        tables = self._components_to_sql(self.table)

        if self.expression:
            sql += self.expression

        elif tables:
            columns = ", ".join(f"{column}" for column in columns) \
                if columns else Star().as_sql()
            sql += f"{columns} FROM {','.join(tables)}"

            if self.join:
                sql += "\n" + self.join.to_sql()

            if self.where:
                sql += " " + self.where.to_sql()

            if self.limit:
                sql += f" LIMIT {self.limit}"

        return sql, []


class QueryParam(Component):
    def __init__(self, type: str, name: str = None, number: int = None):
        self.type = QueryParamStyle[type]
        self.number = number
        self.name = name

    def as_sql(self, add_name: bool = True):
        name = self.name + "=" if self.name and add_name else ""

        return name + self.type.value.format(number=self.number, name=self.name)

    @classmethod
    def from_iterable(cls, type: str, iterable: Iterable[str]) -> "List[QueryParam]":
        query_params = []
        for index, name in enumerate(iterable, 1):
            query_params.append(cls(type, name=name, number=index))

        return query_params


class Value(Component):
    def __init__(self, value, query_param: QueryParam = None):
        self.value = value
        self.query_param = query_param

    def as_sql(self):
        if self.query_param is None:
            raise Exception("Cannot cast to sql because param_type is not specified")
        return self.query_param.as_sql(), [self.value]
