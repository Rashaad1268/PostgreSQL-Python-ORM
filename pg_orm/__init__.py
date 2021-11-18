import logging


def init_db(psycopg2_pool=None, asyncpg_pool=None):
    from pg_orm.models.base_model import Model, AsyncModel
    from pg_orm.models.database import Psycopg2Driver, AsyncpgDriver

    if not psycopg2_pool and not asyncpg_pool:
        raise Exception("psycopg2_pool or asyncpg_pool must be specified.")

    if psycopg2_pool:
        Model.set_db(Psycopg2Driver(psycopg2_pool))

    if asyncpg_pool:
        AsyncModel.set_db(AsyncpgDriver(asyncpg_pool))


logging.getLogger(__name__).addHandler(logging.NullHandler())

__version__ = "0.5.5"
