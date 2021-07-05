import logging

from pg_orm.models.base_model import create_model, Model


logging.getLogger(__name__).addHandler(logging.NullHandler())

__version__ = "0.5.1"