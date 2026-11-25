import asyncio
import sqlite3

import pytest
from databases import Database
from sqlalchemy.exc import IntegrityError

import async_access
import orm_table
import query_params
import transactions
import update_row
from shop import flower, open_shop


@pytest.fixture
def db():
    connection = open_shop()
    yield connection
    connection.close()


def test_set_price(db):
    assert update_row.set_price(db, 1, 200)
    assert flower(db, 1)["price"] == 200
    assert not update_row.set_price(db, 99, 200)


def test_bad_price_is_not_saved(db):
    with pytest.raises(sqlite3.IntegrityError):
        update_row.set_price(db, 1, 0)
    assert flower(db, 1)["price"] == 180


def test_raise_prices(db):
    assert update_row.raise_prices(db, 10, below=150) == 2
    assert [flower(db, i)["price"] for i in (1, 2, 3)] == [180, 99, 143]


def test_add_or_update(db):
    assert update_row.add_or_update(db, "Тюльпан", 95, 30) == (2, 150)
    assert update_row.add_or_update(db, "Ирис", 110, 20) == (6, 20)


def names(rows):
    return [row["name"] for row in rows]


def test_search(db):
    assert names(query_params.cheaper(db, 130)) == ["Тюльпан", "Хризантема"]
    assert names(query_params.search(db, "Роза", low=185)) == ["Роза белая"]
    assert names(query_params.search(db, sort="stock", limit=1)) == [
        "Лилия белая"]
    assert len(query_params.any_of(db, ["Тюльпан", "Мак"])) == 1


def test_parameters_are_safe(db):
    assert query_params.search(db, "' OR 1=1 --") == []
    with pytest.raises(ValueError):
        query_params.search(db, sort="price; DROP TABLE flowers")


@pytest.fixture
def session():
    with orm_table.open_session() as session:
        yield session


def test_orm_queries(session):
    assert [f.name for f in orm_table.in_stock(session, 40)] == [
        "Тюльпан", "Роза красная"]
    assert orm_table.total_cost(session) == 26100
    assert session.get(orm_table.Flower, 4).cost == 2000


def test_orm_sell(session):
    assert orm_table.sell(session, "Тюльпан", 20).stock == 100
    with pytest.raises(ValueError):
        orm_table.sell(session, "Лилия белая", 9)


def test_orm_unique(session):
    session.add(orm_table.Flower(name="Тюльпан", price=1))
    with pytest.raises(IntegrityError):
        session.commit()


@pytest.fixture
def bank():
    connection = transactions.open_bank()
    yield connection
    connection.close()


def test_transfer(bank):
    transactions.transfer(bank, "Анна", "Вера", 400)
    assert transactions.balances(bank) == {"Анна": 600, "Борис": 500,
                                           "Вера": 400}


@pytest.mark.parametrize("args, error", [
    (("Вера", "Анна", 1), transactions.NotEnough),
    (("Анна", "Глеб", 100), KeyError),
    (("Глеб", "Анна", 100), KeyError),
    (("Анна", "Вера", -5), ValueError),
])
def test_failed_transfer_changes_nothing(bank, args, error):
    before = transactions.balances(bank)
    with pytest.raises(error):
        transactions.transfer(bank, *args)
    assert transactions.balances(bank) == before
    assert bank.execute("SELECT count(*) FROM log").fetchone()[0] == 0
    assert not bank.in_transaction


def test_savepoint_keeps_good_payments(bank):
    failed = transactions.pay_all(bank, "Борис", [
        ("Вера", 200), ("Глеб", 10), ("Анна", 5000), ("Анна", 100)])
    assert failed == ["Глеб", "Анна"]
    assert transactions.balances(bank) == {"Анна": 1100, "Борис": 200,
                                           "Вера": 200}


def test_changes_are_invisible_until_commit(tmp_path):
    path = tmp_path / "bank.db"
    first, second = transactions.open_bank(path), transactions.open_bank(path)
    with transactions.transaction(first):
        transactions.move(first, "Анна", "Вера", 100)
        assert transactions.balances(second)["Вера"] == 0
        with pytest.raises(sqlite3.OperationalError):
            transactions.transfer(second, "Анна", "Борис", 1)
    assert transactions.balances(second)["Вера"] == 100
    first.close()
    second.close()


def run_async(tmp_path, action):
    path = (tmp_path / "shop.db").as_posix()
    async_access.create_tables(path)

    async def main():
        async with Database(f"sqlite+aiosqlite:///{path}") as database:
            await async_access.load(database)
            return await action(database)

    return asyncio.run(main())


def test_async_prices(tmp_path):
    result = run_async(tmp_path, lambda db: async_access.prices(
        db, ["Тюльпан", "Мак"]))
    assert result == {"Тюльпан": 90, "Мак": None}


def test_async_sell(tmp_path):
    async def action(db):
        return [await async_access.sell(db, "Лилия белая", 5),
                await async_access.sell(db, "Лилия белая", 5),
                await async_access.sell(db, "Мак", 1),
                (await async_access.find(db, "Лилия"))[0]["stock"]]

    assert run_async(tmp_path, action) == [True, False, False, 3]
