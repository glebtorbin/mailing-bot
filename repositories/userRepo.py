from datetime import datetime, timedelta
from typing import List, Optional

import sqlalchemy as sa
from sqlalchemy.engine import Row

from db.model_users import User, UserTariff
from db.model_nps import Nps
from db.model_payments import Payments, Tariff
from .baseRepo import BaseRepo


class UserRepo(BaseRepo):
    """ `Row` filds: `id`, `first_name`, `last_name`, `username`, `role_id`, `created_at` """

    async def get_all(self, limit: int = 100, skip: int = 0) -> List[Row]:
        query = sa.select(User).limit(limit).offset(skip)
        return await self.database.fetch_all(query)

    async def get_by_id(self, id: str) -> Optional[Row]:
        query = sa.select(User).where(User.id == id)
        return await self.database.fetch_one(query)

    async def get_by_username(self, username: str) -> Optional[Row]:
        query = sa.select(User).where(User.username == username)
        return await self.database.fetch_one(query)
    
    async def get_all_admins(self):
        query = sa.select(User).where(User.role_id == 10)
        return await self.database.fetch_all(query)

    async def create(self, id: str,
                     first_name: Optional[str],
                     last_name: Optional[str],
                     username: Optional[str],
                     role_id: int,
                     phone: str,
                     sphere: str,
                     job_title: str,
                     bot_usage: str,
                     where_from: str) -> int:
        """`return`  id: `int`"""
        user = {
            'id': id,
            'first_name': first_name,
            'last_name': last_name,
            'username': username,
            'role_id': role_id,
            'phone': phone,
            'sphere': sphere,
            'job_title': job_title,
            'bot_usage': bot_usage,
            'where_from': where_from,
            'balance': 0,
            'created_at': datetime.now(),
        }

        query = sa.insert(User).values(**user)
        return await self.database.execute(query)


    async def update(self, id: str, **kwargs) -> int:
        """`return`  id: `int`"""
        query = sa.update(User).where(User.id == id).values(**kwargs)
        return await self.database.execute(query)
    
    async def create_nps(self, service, user_id, username, mark, comment):
        nps = {
            'user_id': user_id,
            'service': service,
            'username': username,
            'mark': mark,
            'comment': comment,
            'created_at': datetime.now()
        }
        query = sa.insert(Nps).values(**nps)
        return await self.database.execute(query)


    async def new_payment(self, user_id, amount, tariff):
        p = {
            'user': user_id,
            'tariff': tariff,
            'amount': amount,
            'created_at': datetime.now()
        }
        query = sa.insert(Payments).values(**p)
        return await self.database.execute(query)


    async def get_u_tariff_by_id(self, user_id):
        query = sa.select(UserTariff).where(UserTariff.is_active==True, UserTariff.user_id==user_id)
        return await self.database.fetch_one(query)

    async def deactivate_u_tariff(self, user_id):
        query = sa.delete(UserTariff).where(UserTariff.user_id == user_id)
        return await self.database.execute(query)

    
    async def create_user_tariff(self, user_id, tariff_id):
        u_rariff = await self.database.fetch_one(sa.select(UserTariff).where(UserTariff.user_id==user_id))
        if not u_rariff:
            p = {
                'tariff': tariff_id,
                'user_id': user_id,
                'is_active': True,
                'start_at': datetime.now(),
                'due_date': datetime.now()+timedelta(weeks=312)
            }
        else:
            p = {
                'tariff': tariff_id,
                'user_id': user_id,
                'is_active': True,
                'start_at': datetime.now(),
                'due_date': datetime.now()+timedelta(days=31)
            }
        query = sa.insert(UserTariff).values(**p)
        return await self.database.execute(query)
    
    async def get_tariff(self, id):
        query = sa.select(Tariff).where(Tariff.id==id)
        return await self.database.fetch_one(query)
    
    async def prolong_u_tariff(self, u_id):
        query = sa.select(UserTariff).where(UserTariff.user_id == u_id)
        u_t = await self.database.fetch_one(query)
        old_due_date = u_t.due_date
        query = sa.update(UserTariff).where(UserTariff.user_id == u_id).values(due_date=old_due_date+timedelta(days=31))
        return await self.database.execute(query)
