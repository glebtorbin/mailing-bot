"""Модели юзеров, ролей, итд"""
from datetime import datetime, timedelta

from sqlalchemy import (BigInteger, Boolean, Column, DateTime, ForeignKey,
                        Integer, String, Table, Text, PrimaryKeyConstraint)

from db.base import Base


class User(Base):
    __tablename__ = 'users'
    __table_args__ = {"comment": "Юзеры"}

    id = Column(String(20), primary_key=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    username = Column(String(50))
    role_id = Column(Integer, ForeignKey('user_role.id'), nullable=False)
    # status_id = Column(Integer, ForeignKey('user_status.id'))
    phone = Column(String(16), nullable=False)
    sphere = Column(String(150))
    job_title = Column(String(150))
    bot_usage = Column(String(150))
    where_from = Column(String(150))
    balance = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now())


class UserRole(Base):
    __tablename__ = 'user_role'
    __table_args__ = {"comment": "Роль юзера"}

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)


class UserTariff(Base):
    __tablename__ = 'user_tariff'
    __table_args__ = (
        PrimaryKeyConstraint('tariff', 'user_id'),
    )

    tariff = Column(Integer, ForeignKey('tariff.id'), nullable=False)
    user_id = Column(String(20), ForeignKey('users.id'), nullable=False)
    is_active = Column(Boolean, nullable=False)
    start_at = Column(DateTime, nullable=False, default=datetime.now())
    due_date = Column(DateTime, nullable=False, default=datetime.now()+timedelta(days=30))