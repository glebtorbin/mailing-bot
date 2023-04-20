from db.base import database

from .userRepo import UserRepo
from .WAClientRepo import WaClientRepo


def get_user_repo() -> UserRepo:
    """ `Row` filds: `id`, `first_name`, `last_name`, `username`, `role_id`, `created_at` """
    return UserRepo(database)

def get_wa_client_repo() -> WaClientRepo:
    return WaClientRepo(database)

