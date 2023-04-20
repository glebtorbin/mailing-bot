from typing import List

from aiogram import types
from sqlalchemy.engine import Row

from enums import WA_Mailing_statuses
from keyboards import get_inline_wa_mailing_markup
from repositories.getRepo import get_user_repo

async def send_WA_mailing(message: types.Message, WA_mailings: List[Row], **kwargs) -> None:
    user_repo = get_user_repo()
    for mai in WA_mailings:
        status = WA_Mailing_statuses(mai.status_id).value
        status_message = f"Статус:  <i>{status['answer']}</i>\n\n"
        creator = await user_repo.get_by_id(mai.creator)
        await message.answer(
            f"Рассылка #{mai.id}\n\n"
            f"Отправлено:  <i>{mai.send}</i>\n"
            f"Всего сообщений:  <i>{mai.for_sending}</i>\n"
            f"Текст: <i>{mai.text}</i>\n\n"
            f"{status_message}", reply_markup=get_inline_wa_mailing_markup(mai), parse_mode="html")

    if kwargs:
        await message.answer("Выберите действие", **kwargs)