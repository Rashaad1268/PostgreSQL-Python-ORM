import asyncio
import asyncpg

from pg_orm import model
from constants import POSTGRESQL_URI

run = asyncio.get_event_loop().run_until_complete
pool = run(asyncpg.create_pool(POSTGRESQL_URI))
Model = model.create_model(pool)

class TestModel(Model):
    name = model.CharField()
