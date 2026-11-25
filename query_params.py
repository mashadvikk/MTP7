from shop import open_shop, print_flowers

SORT = {"name": "name", "price": "price", "stock": "stock"}


def cheaper(db, price):
    return db.execute("SELECT * FROM flowers WHERE price <= ? ORDER BY price",
                      (price,)).fetchall()


def search(db, text="", low=None, high=None, sort="name", limit=10):
    if sort not in SORT:
        raise ValueError(f"сортировка по {sort} невозможна")
    return db.execute(
        f"""SELECT * FROM flowers
            WHERE instr(name, :text) > 0
              AND (:low IS NULL OR price >= :low)
              AND (:high IS NULL OR price <= :high)
            ORDER BY {SORT[sort]} LIMIT :limit""",
        {"text": text, "low": low, "high": high, "limit": limit}).fetchall()


def any_of(db, names):
    places = ",".join("?" for _ in names)
    return db.execute(f"SELECT * FROM flowers WHERE name IN ({places})",
                      list(names)).fetchall()


def main():
    db = open_shop()
    print("Знак ? — цена не выше 180:")
    print_flowers(cheaper(db, 180))
    print("Именованные параметры — розы от 185 руб.:")
    print_flowers(search(db, "Роза", low=185))
    print("Сортировка по остатку, первые 2:")
    print_flowers(search(db, sort="stock", limit=2))
    print("Несколько значений:")
    print_flowers(any_of(db, ["Тюльпан", "Хризантема"]))
    print("Кавычка в данных не ломает запрос:", search(db, "О'Генри"))
    try:
        search(db, sort="price; DROP TABLE flowers")
    except ValueError as error:
        print("Отклонено:", error)
    db.close()


if __name__ == "__main__":
    main()
