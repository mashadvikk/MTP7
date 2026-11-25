from shop import flower, open_shop, print_flowers


def set_price(db, flower_id, price):
    with db:
        cursor = db.execute("UPDATE flowers SET price = ? WHERE id = ?",
                            (price, flower_id))
    return cursor.rowcount == 1


def raise_prices(db, percent, below=None):
    query = "UPDATE flowers SET price = round(price * (100 + ?) / 100.0)"
    values = [percent]
    if below is not None:
        query += " WHERE price < ?"
        values.append(below)
    with db:
        return db.execute(query, values).rowcount


def add_or_update(db, name, price, stock):
    with db:
        row = db.execute(
            """INSERT INTO flowers (name, price, stock) VALUES (?, ?, ?)
               ON CONFLICT (name) DO UPDATE
               SET price = excluded.price, stock = stock + excluded.stock
               RETURNING id, stock""", (name, price, stock)).fetchone()
    return row["id"], row["stock"]


def main():
    db = open_shop()
    print("До изменений:")
    print_flowers(db.execute("SELECT * FROM flowers"))
    print("Новая цена лилии:", set_price(db, 4, 270), flower(db, 4)["price"])
    print("Несуществующая запись:", set_price(db, 99, 100))
    print("Подорожали на 10 %:", raise_prices(db, 10, below=150), "шт.")
    print("Поставка тюльпанов:", add_or_update(db, "Тюльпан", 95, 30))
    print("Новый цветок:", add_or_update(db, "Ирис", 110, 20))
    print("После изменений:")
    print_flowers(db.execute("SELECT * FROM flowers"))
    db.close()


if __name__ == "__main__":
    main()
