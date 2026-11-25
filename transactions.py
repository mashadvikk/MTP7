import sqlite3
from contextlib import contextmanager


class NotEnough(Exception):
    pass


def open_bank(path=":memory:"):
    db = sqlite3.connect(path, isolation_level=None, timeout=0.2)
    db.execute("""CREATE TABLE IF NOT EXISTS accounts (
                      owner TEXT PRIMARY KEY,
                      balance INTEGER NOT NULL CHECK (balance >= 0))""")
    db.execute("""CREATE TABLE IF NOT EXISTS log (
                      id INTEGER PRIMARY KEY, text TEXT NOT NULL)""")
    db.executemany("INSERT OR IGNORE INTO accounts VALUES (?, ?)",
                   [("Анна", 1000), ("Борис", 500), ("Вера", 0)])
    return db


@contextmanager
def transaction(db):
    db.execute("BEGIN IMMEDIATE")
    try:
        yield db
    except BaseException:
        db.execute("ROLLBACK")
        raise
    db.execute("COMMIT")


@contextmanager
def savepoint(db, name="step"):
    db.execute(f"SAVEPOINT {name}")
    try:
        yield db
    except BaseException:
        db.execute(f"ROLLBACK TO {name}")
        db.execute(f"RELEASE {name}")
        raise
    db.execute(f"RELEASE {name}")


def balances(db):
    return dict(db.execute("SELECT owner, balance FROM accounts "
                           "ORDER BY owner"))


def move(db, source, target, amount):
    if amount <= 0:
        raise ValueError("сумма должна быть положительной")
    row = db.execute("SELECT balance FROM accounts WHERE owner = ?",
                     (source,)).fetchone()
    if row is None:
        raise KeyError(source)
    if row[0] < amount:
        raise NotEnough(f"{source}: на счёте {row[0]}, нужно {amount}")
    db.execute("UPDATE accounts SET balance = balance - ? WHERE owner = ?",
               (amount, source))
    cursor = db.execute(
        "UPDATE accounts SET balance = balance + ? WHERE owner = ?",
        (amount, target))
    if cursor.rowcount == 0:
        raise KeyError(target)
    db.execute("INSERT INTO log (text) VALUES (?)",
               (f"{source} -> {target}: {amount}",))


def transfer(db, source, target, amount):
    with transaction(db):
        move(db, source, target, amount)


def pay_all(db, source, payments):
    failed = []
    with transaction(db):
        for target, amount in payments:
            try:
                with savepoint(db):
                    move(db, source, target, amount)
            except (NotEnough, KeyError):
                failed.append(target)
    return failed


def main():
    db = open_bank()
    print("Начало:   ", balances(db))
    transfer(db, "Анна", "Борис", 300)
    print("Перевод:  ", balances(db))
    for source, target, amount in [("Вера", "Анна", 50),
                                   ("Анна", "Глеб", 100)]:
        try:
            transfer(db, source, target, amount)
        except (NotEnough, KeyError) as error:
            print(f"ROLLBACK:  {type(error).__name__} {error}")
    print("Без изменений:", balances(db))
    failed = pay_all(db, "Борис", [("Вера", 200), ("Глеб", 10),
                                   ("Анна", 5000), ("Анна", 100)])
    print("SAVEPOINT: не выполнены", failed)
    print("Итог:     ", balances(db))
    print("Журнал:   ", [row[0] for row in db.execute("SELECT text FROM log")])
    db.close()


if __name__ == "__main__":
    main()
