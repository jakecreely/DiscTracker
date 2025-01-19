from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, BigInteger
from sqlalchemy.orm import relationship, DeclarativeBase

class Base(DeclarativeBase):
    pass

class Item(Base):
    __tablename__ = 'items'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    cex_id = Column(String, nullable=False)
    sell_price = Column(Float, nullable=False)
    exchange_price = Column(Float, nullable=False)
    cash_price = Column(Float, nullable=False)
    last_checked = Column(Date, nullable=False)
    price_history = relationship('PriceHistory', back_populates='item')

class PriceHistory(Base):
    __tablename__ = 'price_history'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    item_id = Column(BigInteger, ForeignKey('items.id'), nullable=False)
    sell_price = Column(Float, nullable=False)
    exchange_price = Column(Float, nullable=False)
    cash_price = Column(Float, nullable=False)
    date_checked = Column(Date, default=None)

    item = relationship('Item', back_populates='price_history')