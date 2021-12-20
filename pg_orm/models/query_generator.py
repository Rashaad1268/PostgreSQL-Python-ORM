import asyncio
import pg_orm

loop = asyncio.get_event_loop()


class QueryGenerator:
    def __init__(self, model):
        self.model = model

    def generate_table_creation_query(self):
        model = self.model
        columns = [f"{field.column_name} {field.to_sql()}" for field in model.fields.values()]
        return "CREATE TABLE IF NOT EXISTS %s (%s)" % (model.table_name, ",\n".join(columns))

    def generate_insert_query(self, return_inserted=False, asyncpg=False, **kwargs):
        model = self.model
        values = []
        for v in kwargs.values():
            if isinstance(v, pg_orm.models.base_model.Model):
                values.append(v.id)
            else:
                values.append(v)

        if not asyncpg:
            col_string = ", ".join(kwargs.keys())
            param_string = ", ".join("%s" for _ in range(len(kwargs.keys())))
            query = f"INSERT INTO {model.table_name} ({col_string}) VALUES({param_string})"

            if return_inserted:
                query += " RETURNING *"

            return query, values

        else:

            col_string = ", ".join(kwargs.keys())
            params = self._get_asyncpg_values(values)
            param_string = ", ".join(params)

            query = f"INSERT INTO {model.table_name} ({col_string}) VALUES({param_string})"
            if return_inserted:
                query += " RETURNING *"

            return query, values

    def generate_update_query(self, asyncpg=False, **kwargs):
        self._check_id(kwargs, "update")
        model = self.model
        id = kwargs["id"]

        if not asyncpg:
            new_values = ", ".join([f"{k}=%s" for k in kwargs.keys()])
            query = f"UPDATE {model.table_name} SET {new_values} WHERE id=%s"
            return query, tuple(kwargs.values()), id
        else:
            values = self._get_asyncpg_values(kwargs)
            new_values = ", ".join(values)
            query = f"UPDATE {self.model.table_name} SET {new_values} WHERE id=${len(values) + 1}"
            return query, tuple(kwargs.values()), id

    def generate_row_deletion_query(self, asyncpg=False, *, column="id", **kwargs):
        # column is a key word argument to prevent it being accidentally passed in
        self._check_id(kwargs, "delete")

        if not asyncpg:
            return f"DELETE FROM {self.model.table_name} WHERE {column}=%s;", kwargs[column]
        else:
            return f"DELETE FROM {self.model.table_name} WHERE {column}=1$", kwargs[column]

    def generate_select_query(self, asyncpg=False, **kwargs):
        if not asyncpg:
            params = [f"{key}=%s" for key in kwargs.keys()]
            query = "SELECT * FROM {0} WHERE {1};".format(
                self.model.table_name, " AND ".join(params)
            )
            return query, tuple(kwargs.values())

        else:
            params = self._get_asyncpg_values(kwargs)
            query = "SELECT * FROM {0} WHERE {1};".format(
                self.model.table_name, " AND ".join(params)
            )
            return query, tuple(kwargs.values())

    def _check_id(self, data: dict, operation: str = "operation"):
        if data.get("id") is None:
            raise Exception(f"Cannot {operation} row without id specified.")

    def _get_asyncpg_values(self, data):
        if isinstance(data, dict):
            return [f"{k}=${i + 1}" for i, k in enumerate(data.keys())]
        elif isinstance(data, list):
            return [f"${i + 1}" for i, k in enumerate(data)]

    def _get_psycopg2_values(self, data: dict):
        return [f"{k}=%s" for k in data.keys()]
