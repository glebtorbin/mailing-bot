from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, DateTime
import datetime

from db.base import Base

class Tariff(Base):
    __tablename__ = 'tariff'
    __table_args__ = {"comment": "тарифы"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50))
    slug = Column(String(50))
    price = Column(Integer, nullable=False, comment='Цена в копейках')
    day_limit = Column(Integer, nullable=False, comment='Дневной лимит сообщений')


class Payments(Base):
    __tablename__ = 'payments'
    __table_args__ = {"comment": "платежи"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    user = Column(String(20), ForeignKey('users.id'), nullable=False)
    amount = Column(Integer, nullable=False)
    tariff = Column(Integer, ForeignKey('tariff.id'), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.now())