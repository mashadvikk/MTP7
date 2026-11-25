import asyncio
import os
import tempfile

import sqlalchemy as sa
from databases import Database

from shop import FLOWERS

metadata = sa.MetaData()
flowers = sa.Table(
    "flowers", metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("name", sa.String(40), nullable=False, unique=True),
    sa.Column("price", sa.Integer, nullable=False),
    sa.Column("stock", sa.Integer, nullable=False),
)


def create_tables(path):
    engine = sa.create_engine(f"sqlite:///{path}")
    metadata.create_all(engine)
    engine.dispose()


async def load(database):
    await database.execute_many(flowers.insert(), [
        {"name": name, "price": price, "stock": stock}
        for name, price, stock in FLOWERS])


async def find(database, text):
    query = flowers.select().where(flowers.c.name.like(f"%{text}%"))
    return [dict(row) for row in
            await database.fetch_all(query.order_by(flowers.c.id))]


async def price_of(database, name):
    return await database.fetch_val(
        sa.select(flowers.c.price).where(flowers.c.name == name))


async def prices(database, names):
    values = await asyncio.gather(*(price_of(database, name)
                                    for name in names))
    return dict(zip(names, values))


async def sell(database, name, count):
    async with database.transaction():
        row = await database.fetch_one(
            flowers.select().where(flowers.c.name == name))
        if row is None or row["stock"] < count:
            return False
        await database.execute(
            flowers.update().where(flowers.c.id == row["id"])
            .values(stock=flowers.c.stock - count))
    return True


async def demo(path):
    create_tables(path)
    async with Database(f"sqlite+aiosqlite:///{path}") as database:
        await load(database)
        print("Поиск «Роза»:", await find(database, "Роза"))
        print("Цены одновременно:",
              await prices(database, ["Тюльпан", "Лилия белая", "Мак"]))
        print("Продать 5 лилий:", await sell(database, "Лилия белая", 5))
        print("Продать ещё 5:", await sell(database, "Лилия белая", 5))
        print("Остаток:", (await find(database, "Лилия"))[0]["stock"])


def main():
    with tempfile.TemporaryDirectory() as folder:
        asyncio.run(demo(os.path.join(folder, "shop.db").replace("\\", "/")))


if __name__ == "__main__":
    main()
