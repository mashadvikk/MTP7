from sqlalchemy import CheckConstraint, String, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from shop import FLOWERS


class Base(DeclarativeBase):
    pass


class Flower(Base):
    __tablename__ = "flowers"
    __table_args__ = (CheckConstraint("price > 0"),
                      CheckConstraint("stock >= 0"))

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40), unique=True)
    price: Mapped[int]
    stock: Mapped[int] = mapped_column(default=0)

    @property
    def cost(self):
        return self.price * self.stock

    def __repr__(self):
        return f"<{self.name}: {self.price} руб., {self.stock} шт.>"


def open_session(url="sqlite://", echo=False):
    engine = create_engine(url, echo=echo)
    Base.metadata.create_all(engine)
    session = Session(engine)
    if not session.scalar(select(func.count(Flower.id))):
        session.add_all(Flower(name=name, price=price, stock=stock)
                        for name, price, stock in FLOWERS)
        session.commit()
    return session


def in_stock(session, minimum):
    return session.scalars(select(Flower).where(Flower.stock >= minimum)
                           .order_by(Flower.stock.desc())).all()


def total_cost(session):
    return session.scalar(select(func.sum(Flower.price * Flower.stock)))


def sell(session, name, count):
    flower = session.scalars(select(Flower).where(Flower.name == name)).one()
    if flower.stock < count:
        raise ValueError(f"осталось только {flower.stock} шт.")
    flower.stock -= count
    session.commit()
    return flower


def main():
    with open_session() as session:
        print("Все:", session.scalars(select(Flower)).all())
        print("Не меньше 25 шт.:", in_stock(session, 25))
        print("Стоимость запасов:", total_cost(session))
        print("Продано 5 роз:", sell(session, "Роза красная", 5))
        try:
            sell(session, "Лилия белая", 10)
        except ValueError as error:
            print("Не продано:", error)
        session.delete(session.get(Flower, 5))
        session.commit()
        print("Осталось видов:", session.scalar(select(func.count(Flower.id))))


if __name__ == "__main__":
    main()
