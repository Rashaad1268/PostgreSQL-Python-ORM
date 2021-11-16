class SchemaDifference:
    """Compares the migrations to the current state of the model"""

    def __init__(self, model, before: dict):
        """"""
        self.model = model
        self.before = model.from_dict(before)

    @staticmethod
    def get_field_comparable_id(field):
        """An id which can be used to compare two fields"""
        return '-'.join('%s:%s' % (attr, getattr(field, attr)) for attr in ("column_name", "validators", "is_unique",
                                                                            "primary_key", "nullable", "default",
                                                                            "default_insertion_value"))

    def field_is_renamed(self, first, second):
        if first.column_name == second.column_name:
            return False

        return first.is_unique == second.is_unique and first.primary_key == second.primary_key

    def to_sql(self):
        before = self.before
        current = self.model
        base = f"ALTER TABLE {before.table_name}\n"
        statements = []
        get_id = self.get_field_comparable_id

        if len(before.fields) == len(current.fields):
            for c, b in zip(current.fields, before.fields):
                alter_col = f"ALTER COLUMN {b.column_name}"

                if get_id(c) == get_id(b):
                    continue  # Nothing has changed

                if self.field_is_renamed(b, c):
                    statements.append(base + f"RENAME COLUMN {b.column_name} TO {c.column_name}")

                elif b.nullable != c.nullable:
                    set_or_drop = "DROP" if b.nullable is True and c.nullable is False else "SET"
                    statements.append(base + f"{alter_col} {set_or_drop} NOT NULL")

                elif b.default != c.default:
                    set_or_drop = f"SET DEFAULT {c._get_default_val()}" if c.default is not None else "DROP DEFAULT"
                    statements.append(base + f"{alter_col} {b.column_name} {set_or_drop}")

        elif len(before.fields) < len(current.fields):
            # Get the fields which are newly added We have to use this method instead of
            # list(set(before.fields) - set(current.fields)) since fields are not hashable
            newly_added_fields = [x for x in current.fields if
                                  get_id(x) not in [get_id(y) for y in before.fields]]
            add_fields_query = [f"ADD COLUMN {field.column_name} {field.to_sql()}" for field in newly_added_fields]
            statements.append(base + ", ".join(add_fields_query))

        elif len(before.fields) > len(current.fields):
            # Get the fields which are removed

            # We have to use this method instead of list(set(current.fields) - set(before.fields))
            # since fields are not hashable
            removed_fields = [x for x in before.fields if
                              get_id(x) not in [get_id(y) for y in current.fields]]
            drop_fields_query = [f"DROP COLUMN IF EXISTS {field.column_name}" for field in removed_fields]
            statements.append(base + ", ".join(drop_fields_query))

        if before.table_name != current.table_name:
            statements.append(base + f"RENAME TO {current.table_name}")

        if not statements:
            return None  # Return None if nothing has changed

        else:
            return statements
