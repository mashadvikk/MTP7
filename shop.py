import sqlite3

FLOWERS = [
    ("Роза красная", 180, 40),
    ("Тюльпан", 90, 120),
    ("Хризантема", 130, 25),
    ("Лилия белая", 250, 8),
    ("Роза белая", 190, 15),
]


def open_shop(path=":memory:"):
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("""CREATE TABLE IF NOT EXISTS flowers (
                      id INTEGER PRIMARY KEY,
                      name TEXT NOT NULL UNIQUE,
                      price INTEGER NOT NULL CHECK (price > 0),
                      stock INTEGER NOT NULL CHECK (stock >= 0))""")
    if db.execute("SELECT count(*) FROM flowers").fetchone()[0] == 0:
        db.executemany("INSERT INTO flowers (name, price, stock) "
                       "VALUES (?, ?, ?)", FLOWERS)
    db.commit()
    return db


def flower(db, flower_id):
    return db.execute("SELECT * FROM flowers WHERE id = ?",
                      (flower_id,)).fetchone()


def print_flowers(rows):
    for row in rows:
        print(f"  {row['id']}. {row['name']:<14}{row['price']:>5} руб."
              f"{row['stock']:>5} шт.")
