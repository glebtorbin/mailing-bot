#!venv/bin/python
import logging
import requests
import logging.handlers as loghandlers
from buttons import ClientBts, Bts
import os
from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor

from answers import send_WA_mailing
from wapp.wa_xlsx_scrap import WA_xlsx_search
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import get_bot_token
from db.base import database
from keyboards import (
    get_admin_markup, get_user_markup, wa_check_qr_markup,
    wa_save_correct_phones_markup, wa_save_mailing_markup,
    get_inline_wa_mailing_cont_markup,
    get_inline_wa_client_markup,
    get_inline_wa_mailing_correct_markup,
    get_inline_wa_mailing_markup,
    get_inline_wa_mailing_stop_markup,
    pay_markup, prolong_markup, support_markup,
    nps_markup
)
from state import GlobalState, ClientState
from aiogram import types
from aiogram.dispatcher import FSMContext
from messages import User_messages, Urls, Error_messages, Pay_messages
from enums import URoles, WA_CStatuses, WA_CWorkes, WA_Mailing_statuses
from keyboards import (
    user_accept_markup, sphere_markup, work_markup,
    bot_usage_markup,
    send_contact_markup,
    wa_check_qr_markup, cancel_markup, change_tariff_markup
)
from wapp.wa_api import wa_check_state, wa_get_acc_settings, wa_logout, wa_mailing, wa_reboot, wa_send_qr
from repositories.getRepo import get_user_repo, get_wa_client_repo
from state import GlobalState, ClientState
from aiogram.dispatcher.filters import Text

storage = MemoryStorage()

TG_TOKEN = get_bot_token()

bot = Bot(token=TG_TOKEN)
dp = Dispatcher(bot, storage=storage)
scheduler = AsyncIOScheduler()

async def create_folders():
    for folder in ['logs', 'qr', 'wa_mailing_contacts']:
        if not os.path.exists(folder):
            os.makedirs(folder)


LOGGER = logging.getLogger('applog')
LOGGER.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s  %(filename)s  %(funcName)s  %(lineno)d  %(name)s  %(levelname)s: %(message)s')
log_handler = loghandlers.RotatingFileHandler(
    './logs/botlog.log',
    maxBytes=1000000,
    encoding='utf-8',
    backupCount=50
)
log_handler.setLevel(logging.INFO)
log_handler.setFormatter(formatter)
LOGGER.addHandler(log_handler)


# MAIN_MARKUP = get_admin_markup((Bts.ACCOUNTS.value, Bts.GROUPS.value), (Bts.SERVICES.value, Bts.WA_ACCS.value))

MAIN_CL_MARKUP = get_user_markup((
    Bts.MAILINGS.value, Bts.ACCS.value),
    (Bts.TARIF.value, Bts.SUP.value))



async def on_startup(dp):
    """Соединяемся с БД при запуске бота."""
    try:
        await database.connect()
        await create_folders()
        LOGGER.info('DB is running')
        LOGGER.info('service folders created')
    except Exception as err:
        LOGGER.critical(f'Не подключается БД! {err}')


@dp.message_handler(commands='start', state=None)
async def start(message: types.Message, state: FSMContext):
    try:
        args = message.get_args()
        async with state.proxy() as data:
            data['where_from'] = args
            data['user_id'] = message.from_user.id
        u_repo = get_user_repo()
        user = await u_repo.get_by_id(message.chat.id)
        if user is None:
            await message.answer(User_messages.HELLO.value,
                                 parse_mode='html',
                                disable_web_page_preview=True, reply_markup=user_accept_markup())
            await ClientState.accept.set()
        elif user.role_id == URoles.ADMIN.value['id']:
            await GlobalState.admin.set()
            await message.answer(User_messages.IN_MAIN.value, reply_markup=MAIN_CL_MARKUP)
        elif user.role_id == URoles.USER.value['id']:
            await ClientState.client.set()
            await message.answer(User_messages.IN_MAIN.value, reply_markup=MAIN_CL_MARKUP)
        else:
            await message.answer(Error_messages.REG_ERROR.value)
    except Exception as err:
        LOGGER.error(f'Ошибка функции start: {err}')


@dp.message_handler(Text(equals=Bts.GO_TO_MAIN.value), state=ClientState.client)
async def go_to_main(message: types.Message):
    await message.answer(User_messages.IN_MAIN.value, reply_markup=MAIN_CL_MARKUP)

@dp.message_handler(Text(equals=ClientBts.ACCEPT_POLICY.value), state=ClientState.accept)
async def reg_menu_ask_phone(message: types.Message, state: FSMContext):
    try:
        await state.set_state(ClientState.send_phone_code)
        await message.answer(
            User_messages.REG_NUMBER.value,
            reply_markup=send_contact_markup()
        )
    except Exception as err:
        LOGGER.error(err)

@dp.message_handler(content_types=types.ContentType.CONTACT, state=ClientState.send_phone_code)
async def reg_menu_send_phone_code(message: types.message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['cl_phone'] = message.contact.phone_number
        await state.set_state(ClientState.about_1)

        ph = await bot.send_photo(message.from_user.id, open('img/About_yourself.jpg', 'rb'))
        async with state.proxy() as data:
            data['photo_id'] = ph.message_id
        await message.answer(User_messages.REG_SPHERE.value, reply_markup=sphere_markup())
    except Exception as err:
        LOGGER.error(err)


@dp.callback_query_handler(text_contains='sphere:', state=ClientState.about_1)
async def reg_menu_sphere_ask(call: types.CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
        async with state.proxy() as data:
            data['cl_sphere'] = (call.data).split(':')[1]
        await state.set_state(ClientState.about_2)
        await call.message.answer(User_messages.REG_WORK.value, reply_markup=work_markup())
    except Exception as err:
        LOGGER.error(err)


@dp.callback_query_handler(text_contains='work:', state=ClientState.about_2)
async def reg_menu_bot_usage(call: types.CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
        async with state.proxy() as data:
            data['cl_job_title'] = (call.data).split(':')[1]
        await state.set_state(ClientState.about_3)
        await call.message.answer(User_messages.REG_USAGE.value, reply_markup=bot_usage_markup())
    except Exception as err:
        LOGGER.error(err)


@dp.callback_query_handler(text_contains='usage:', state=ClientState.about_3)
async def reg_menu_save_answers(call: types.CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
        u_repo = get_user_repo()
        async with state.proxy() as data:
            data['cl_bot_usage'] = (call.data).split(':')[1]
            await u_repo.create(
                id= str(call.from_user.id),
                first_name=call.message.chat.first_name,
                last_name=call.message.chat.last_name,
                username=call.message.chat.username,
                role_id=URoles.USER.value['id'],
                phone=data['cl_phone'],
                sphere=data['cl_sphere'],
                job_title=data['cl_job_title'],
                bot_usage=data['cl_bot_usage'],
                where_from=data['where_from']
            )
        await u_repo.create_user_tariff(str(call.from_user.id), 1)
        await state.set_state(ClientState.client)
        # await call.message.answer('Регистрация пройдена успешно!')
        async with state.proxy() as data:
            await bot.delete_message(chat_id=call.from_user.id, message_id=data['photo_id'])
        await bot.send_photo(call.from_user.id, open('img/End_reg.jpg', 'rb'))
        #TODO Тут судя по тексту в документе должен быть обущающий ролик
        await call.message.answer(User_messages.IN_MAIN.value, reply_markup=MAIN_CL_MARKUP)
    except Exception as err:
        LOGGER.critical(f'Ошибка создания профайла юзера {err}')
        await call.message.answer(Error_messages.MAIN_ERROR.value)


@dp.message_handler(Text(equals=Bts.SUP.value), state=ClientState.client)
async def my_support(message: types.Message):
    await bot.send_photo(
        chat_id=message.from_user.id,
        photo=open('img/support.jpg', 'rb'),
        reply_markup=support_markup()
    )


@dp.callback_query_handler(text_contains='npsque', state=ClientState.client)
async def nps_ask(call: types.CallbackQuery):
    await call.message.answer(
        User_messages.NPS.value,
        reply_markup=nps_markup()
    )


@dp.callback_query_handler(text_contains='nps', state=ClientState.client)
async def nps_save(call: types.CallbackQuery):
    try:
        user_repo = get_user_repo()
        await user_repo.create_nps(
            user_id=str(call.from_user.id),
            service="mailing",
            username=call.from_user.username or '',
            mark=call.data.split(':')[-1],
            comment="no comment"
        )
        await call.message.delete()
        await call.message.answer('Спасибо!', reply_markup=MAIN_CL_MARKUP)
    except Exception as err:
        LOGGER.error(err)


@dp.message_handler(Text(equals=Bts.TARIF.value), state=ClientState.client)
async def my_tariff(message: types.Message):
    u_repo = get_user_repo()
    u_tariff = await u_repo.get_u_tariff_by_id(str(message.from_user.id))
    tariff_info = await u_repo.get_tariff(u_tariff.tariff)
    await bot.send_photo(
        chat_id=message.from_user.id,
        photo=open('img/mytariff.jpg', 'rb'),
        caption=User_messages.U_TARIFF.value.format(
            name=tariff_info.name,
            limit=tariff_info.day_limit,
            price=int(tariff_info.price/100),
            due_date=(u_tariff.due_date).date().strftime("%d.%m.%Y")
        ),
        reply_markup=change_tariff_markup(tariff_info.id)
    )


@dp.callback_query_handler(text_contains='prolongpay:', state=ClientState.client)
async def prolong_payment_ans(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(
        Pay_messages.ORDER_NUM.value
    )
    await ClientState.prolongpay.set()


@dp.message_handler(state=ClientState.prolongpay)
async def prolong_payment(message: types.Message, state: FSMContext):
    order_id = message.text
    user_repo = get_user_repo()
    endpoint = f'https://invite-robot.ru/api/get_payment/{order_id}/'
    info = requests.get(endpoint)
    user = await user_repo.get_by_id(str(message.from_user.id))
    user_tariff = await user_repo.get_u_tariff_by_id(user.id)
    tariff_info = await user_repo.get_tariff(user_tariff.tariff)
    try:
        if info.json()[0]['Amount'] and info.json()[0]['Confirmed'] == False:
            if info.json()[0]['Amount'] == tariff_info.price:
                await ClientState.client.set()
                await user_repo.prolong_u_tariff(user.id)
                await message.answer(Pay_messages.PROLONG_OK.value,
                reply_markup=MAIN_CL_MARKUP)
                requests.get(f'https://invite-robot.ru/api/confirm_payment/{order_id}/')
                await user_repo.new_payment(message.from_user.id, 100, 2)
            else:
                await message.answer(Pay_messages.UNKNOWN_AMOUNT.value, reply_markup=MAIN_CL_MARKUP)
                await ClientState.client.set()
        else:
            await message.answer(Pay_messages.UNKNOWN_NUM.value, reply_markup=MAIN_CL_MARKUP)
            await ClientState.client.set()
    except Exception as er:
        LOGGER.critical(er)
        await message.answer(Pay_messages.UNKNOWN_NUM.value, reply_markup=MAIN_CL_MARKUP)
        await ClientState.client.set()


@dp.callback_query_handler(text_contains='checkpay:', state=ClientState.client)
async def check_payment_ans(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(
        Pay_messages.ORDER_NUM.value
    )
    current_state = await state.get_state()
    print(current_state)
    async with state.proxy() as data:
        data['cur_state'] = current_state
        data['amount'] = call.data.split(':')[-1]
    await ClientState.check_paym.set()


@dp.message_handler(state=ClientState.check_paym)
async def check_payment(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        cur_state = data['cur_state']
        amount = data['amount']
    order_id = message.text
    user_repo = get_user_repo()
    endpoint = f'https://invite-robot.ru/api/get_payment/{order_id}/'
    info = requests.get(endpoint)
    user = await user_repo.get_by_id(str(message.from_user.id))
    user_bl = user.balance
    try:
        print(info.json()[0]['Amount'], amount)
        if info.json()[0]['Amount'] and info.json()[0]['Confirmed'] == False:
            bl=info.json()[0]['Amount']//100
            if info.json()[0]['Amount'] == 100:
                await ClientState.client.set()
                await user_repo.deactivate_u_tariff(str(message.from_user.id))
                await user_repo.create_user_tariff(str(message.from_user.id), 2)
                await message.answer(Pay_messages.EFFECTIVE_OK.value,
                reply_markup=MAIN_CL_MARKUP)
                requests.get(f'https://invite-robot.ru/api/confirm_payment/{order_id}/')
                await user_repo.new_payment(message.from_user.id, 100, 2)
            elif info.json()[0]['Amount'] == 200:
                await ClientState.client.set()
                await user_repo.deactivate_u_tariff(str(message.from_user.id))
                await user_repo.create_user_tariff(str(message.from_user.id), 3)
                await message.answer(Pay_messages.ALLIN_OK.value,
                reply_markup=MAIN_CL_MARKUP)
                requests.get(f'https://invite-robot.ru/api/confirm_payment/{order_id}/')
                await user_repo.new_payment(message.from_user.id, 200, 3)
            else:
                await message.answer(Pay_messages.UNKNOWN_AMOUNT.value, reply_markup=MAIN_CL_MARKUP)
                await ClientState.client.set()
        else:
            await message.answer(Pay_messages.UNKNOWN_NUM.value, reply_markup=MAIN_CL_MARKUP)
            await ClientState.client.set()
    except Exception as er:
        LOGGER.critical(er)
        await message.answer(Pay_messages.UNKNOWN_NUM.value, reply_markup=MAIN_CL_MARKUP)
        await ClientState.client.set()


@dp.callback_query_handler(text_contains='tariff_change:', state=ClientState.client)
async def tariff_change(call: types.CallbackQuery):
    await call.message.delete()
    await bot.send_photo(chat_id=call.message.chat.id, photo=open('img/tariffes.jpg', 'rb'), reply_markup=pay_markup(call.from_user.id))


@dp.callback_query_handler(text_contains='tariff_prolong:', state=ClientState.client)
async def tariff_prolong(call: types.CallbackQuery):
    await call.message.delete()
    id = call.data.split(':')[-1]
    user_repo = get_user_repo()
    tariff = await user_repo.get_tariff(int(id))
    await call.message.answer(
        Pay_messages.PROLONG_TARIFF.value,
        reply_markup=prolong_markup(call.from_user.id, int(tariff.price/100))
    )


async def wa_auth(call: types.CallbackQuery, state: FSMContext):
    try:
        wa_repo = get_wa_client_repo()
        client_id = call.data.split(':')[-1]
        client_data = await wa_repo.get_by_id(client_id)
        async with state.proxy() as data:
            data['wa_client_data'] = client_data
        wa_acc_state = await wa_check_state(client_data)
        if wa_acc_state == 'notAuthorized':
            await GlobalState.wa_send_qr.set()
            await wa_send_qr(client_data)
            qr = open(f'./qr/qr_{client_data.id_instance}.png', 'rb')
            await bot.send_photo(call.from_user.id, qr, reply_markup=cancel_markup())
            qr.close()
            path = os.path.join(
                os.path.abspath(os.path.dirname(__file__)), f'./qr/qr_{client_data.id_instance}.png'
            )
            os.remove(path)
            await call.message.answer(
                'Отсканируйте QR-code в мобильном приложении Whatsapp',
                reply_markup=wa_check_qr_markup(client_data)
            )
        elif wa_acc_state == 'authorized':
            phone = await wa_get_acc_settings(client_data)
            await wa_repo.update(client_data.id, phone = phone['wid'],status_id=WA_CStatuses.AUTHORIZED.value['id'])
            await call.message.answer('Аккаунт успешно авторизован', reply_markup=MAIN_CL_MARKUP)
        elif wa_acc_state == 'blocked':
            await wa_repo.update(client_data.id, phone = 'not authorized', status_id=WA_CStatuses.BANNED.value['id'])
            await call.message.answer('Аккаунт заблокирован', reply_markup=MAIN_CL_MARKUP)
        else:
            await call.message.answer(
                'Аккаунт либо в спящем режиме, либо в процессе запуска. Попробуйте позже',
                reply_markup=MAIN_CL_MARKUP
            )
    except Exception as err:
        LOGGER.error(err)


async def wa_check_auth(call: types.CallbackQuery):
    try:
        wa_repo = get_wa_client_repo()
        client_id = call.data.split(':')[-1]
        client_data = await wa_repo.get_by_id(client_id)
        wa_acc_state = await wa_check_state(client_data)
        if wa_acc_state == 'authorized':
            await GlobalState.admin.set()
            phone = await wa_get_acc_settings(client_data)
            await wa_repo.update(client_data.id, phone = phone['wid'],status_id=WA_CStatuses.AUTHORIZED.value['id'])
            await call.message.answer('Аккаунт успешно авторизован', reply_markup=MAIN_CL_MARKUP)
        else:
            await call.message.answer(
                'Что-то пошло не так. Попробуйте еще раз',
                reply_markup=cancel_markup()
            )
    except Exception as err:
        LOGGER.error(err)


async def WA_logout(call: types.CallbackQuery):
    try:
        wa_repo = get_wa_client_repo()
        client_id = call.data.split(':')[-1]
        client_data = await wa_repo.get_by_id(client_id)
        wa_acc_state = await wa_check_state(client_data)
        if wa_acc_state == 'authorized':
            logout = await wa_logout(client_data)
            if logout == True:
                await wa_repo.update(
                    client_data.id, phone = 'not authorized',
                    status_id=WA_CStatuses.WAITING_AUTHORIZATION.value['id']
                )
                await call.message.answer('Аккаунт успешно разлогинен', reply_markup=MAIN_CL_MARKUP)
            else:
                await call.message.answer(
                    'Что-то пошло не так. Попробуйте еще раз',
                    reply_markup=cancel_markup()
                )
        elif wa_acc_state == 'notAuthorized':
            await wa_repo.update(
                    client_data.id, phone = 'not authorized',
                    status_id=WA_CStatuses.WAITING_AUTHORIZATION.value['id']
                )
            await call.message.answer('Аккаунт успешно разлогинен', reply_markup=MAIN_CL_MARKUP)
        elif wa_acc_state == 'blocked':
            await wa_repo.update(client_data.id, phone = 'not authorized', status_id=WA_CStatuses.BANNED.value['id'])
            await call.message.answer('Аккаунт заблокирован, требуется авторизовать новый аккаунт', reply_markup=MAIN_CL_MARKUP)
        else:
            await call.message.answer(f'Статус аккаунта: {wa_acc_state}', reply_markup=MAIN_CL_MARKUP)
    except Exception as err:
        LOGGER.error(err)


async def WA_reboot(call: types.CallbackQuery):
    try:
        wa_repo = get_wa_client_repo()
        client_id = call.data.split(':')[-1]
        client_data = await wa_repo.get_by_id(client_id)
        wa_acc_state = await wa_check_state(client_data)
        if wa_acc_state == 'authorized':
            reboot = await wa_reboot(client_data)
            if reboot == True:
                await call.message.answer('Аккаунт успешно перезапущен', reply_markup=MAIN_CL_MARKUP)
            else:
                await call.message.answer(
                    'Что-то пошло не так. Попробуйте еще раз',
                    reply_markup=cancel_markup()
                )
        elif wa_acc_state == 'notAuthorized':
            await wa_repo.update(
                    client_data.id, phone = 'not authorized',
                    status_id=WA_CStatuses.WAITING_AUTHORIZATION.value['id']
                )
            await call.message.answer('Аккаунт не авторизован!', reply_markup=MAIN_CL_MARKUP)
        elif wa_acc_state == 'blocked':
            await wa_repo.update(client_data.id, phone = 'not authorized', status_id=WA_CStatuses.BANNED.value['id'])
            await call.message.answer('Аккаунт заблокирован, требуется авторизовать новый аккаунт', reply_markup=MAIN_CL_MARKUP)
        else:
            await call.message.answer(f'Статус аккаунта: {wa_acc_state}', reply_markup=MAIN_CL_MARKUP)
    except Exception as err:
        LOGGER.error(err)


async def WA_delete(call: types.CallbackQuery):
    try:
        wa_repo = get_wa_client_repo()
        client_id = call.data.split(':')[-1]
        client_data = await wa_repo.get_by_id(client_id)
        wa_acc_state = await wa_check_state(client_data)
        if wa_acc_state == 'authorized':
            logout = await wa_logout(client_data)
            if logout == True:
                LOGGER.info('Инстанс был авторизовн и перед удалением был разлогинен')
            else:
                LOGGER.debug('Не получилось разлогинить инстанс перед удалением')
        await wa_repo.delete(client_data.id)
        await call.message.delete()
        await call.message.answer('Инстанс успешно удален', reply_markup=MAIN_CL_MARKUP)
    except Exception as er:
        LOGGER.error(er)
        await call.message.answer(f'Что-то пошло не так: {er}', reply_markup=MAIN_CL_MARKUP)


@dp.message_handler(Text(equals=Bts.MAILINGS.value), state=ClientState.client)
async def send_wa_mailing(message: types.Message):
    wa_repo = get_wa_client_repo()
    try:
        mailings = await wa_repo.get_mailings_by_creator(message.from_user.id)
        markup = get_admin_markup((Bts.GO_TO_MAIN.value, Bts.NEW_MAILING.value))
        await bot.send_photo(chat_id=message.from_user.id, photo=open('img/mailings.jpg', 'rb'))
        if len(mailings):
            await send_WA_mailing(message=message, WA_mailings=mailings, reply_markup=markup)
        else:
            await message.answer(User_messages.NO_MAILINGS.value, reply_markup=markup)
    except Exception as err:
        await message.answer(Error_messages.MAIN_ERROR.value)
        LOGGER.error(err)


@dp.message_handler(Text(equals=Bts.NEW_MAILING.value), state=ClientState.client)
async def WA_mailing(message: types.Message):
    await message.answer(
        User_messages.XLSX_FILE.value,
        reply_markup=cancel_markup()
    )
    await GlobalState.wa_mailing_file.set()


@dp.message_handler(content_types=[types.ContentType.DOCUMENT, ], state=GlobalState.wa_mailing_file)
async def WA_mailing_message(message: types.Message, state: FSMContext):
    try:
        file = await bot.get_file(message.document.file_id)
        file_path = file.file_path
        await bot.download_file(file_path, f"./wa_mailing_contacts/wa_{message.from_user.id}.xlsx")
        phones, count_phones = await WA_xlsx_search('phone', message.from_user.id)
        async with state.proxy() as data:
            data['phones'], data['count_phones'] = phones, count_phones
        path = os.path.join(
                os.path.abspath(os.path.dirname(__file__)), f'./wa_mailing_contacts/wa_{message.chat.id}.xlsx'
        )
        os.remove(path)
        await GlobalState.wa_mailing_message.set()
        await message.answer(f'Найдено {count_phones} номеров для рассылки')
        await message.answer('Напишите текст для отправки', reply_markup=cancel_markup())
    except Exception as err:
        LOGGER.error(err)

@dp.message_handler(state=GlobalState.wa_mailing_message)
async def WA_mailing_info(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['wa_mailing_text'] = message.text
            count_phones = data['count_phones']
        await message.answer(
            f'Кол-во номеров телефонов для рассылки: {count_phones}\n\n'
            'текст сообщения:\n'
            f'{message.text}',
            reply_markup=wa_save_mailing_markup()
        )
    except Exception as err:
        LOGGER.error(err)

@dp.callback_query_handler(text_contains='wa_client:save_mailing', state=GlobalState.wa_mailing_message)
async def WA_mailing_save(call: types.CallbackQuery, state: FSMContext):
    try:
        async with state.proxy() as data:
            for_sending = data['count_phones']
            phones = data['phones']
            text = data['wa_mailing_text']
        wa_repo = get_wa_client_repo()
        await wa_repo.create_mailing(
             call.from_user.id, WA_Mailing_statuses.UNWORKING.value['id'], for_sending, text, phones
        )
        await ClientState.client.set()
        await call.message.edit_reply_markup(reply_markup=None)
        await call.message.answer('Рассылка успешно сохранена', reply_markup=MAIN_CL_MARKUP)
    except Exception as err:
        LOGGER.error(err)
        await ClientState.client.set()
        await call.message.answer(f'Что-то пошло не так, попробуйте позже\n\n{err}', reply_markup=MAIN_CL_MARKUP)


@dp.callback_query_handler(text_contains='wa_mailing:mailing_start:', state=ClientState.client)
async def WA_mailing_start(call: types.CallbackQuery, state: FSMContext):
    try:
        mai_id = call.data.split(':')[-1]
        wa_repo = get_wa_client_repo()
        mai = await wa_repo.get_mailing_by_id(mai_id)
        await wa_repo.mailing_update(mai_id, status_id=WA_Mailing_statuses.WORKING.value['id'])
        await call.message.answer('Рассылка запущена')
        await call.message.edit_reply_markup(reply_markup=get_inline_wa_mailing_cont_markup(mai))
        await wa_mailing(mai_id)
    except Exception as err:
        LOGGER.error(err)


@dp.callback_query_handler(text_contains='wa_mailing:mailing_stop:', state=ClientState.client)
async def WA_mailing_stop(call: types.CallbackQuery):
    try:
        mai_id = call.data.split(':')[-1]
        wa_repo = get_wa_client_repo()
        mai = await wa_repo.get_mailing_by_id(mai_id)
        await wa_repo.mailing_update(mai_id, status_id=WA_Mailing_statuses.PAUSED.value['id'])
        await call.message.edit_reply_markup(reply_markup=get_inline_wa_mailing_stop_markup(mai))
        await call.message.answer('Рассылка остановлена')
    except Exception as err:
        LOGGER.error(err)


@dp.callback_query_handler(text_contains='wa_mailing:mailing_delete:', state=ClientState.client)
async def WA_mailing_delete(call: types.CallbackQuery):
    try:
        mai_id = call.data.split(':')[-1]
        wa_repo = get_wa_client_repo()
        await wa_repo.mailing_phones_delete(mai_id)
        await wa_repo.mailing_delete(mai_id)
        await call.message.delete()
        await call.message.answer('Рассылка удалена')
    except Exception as err:
        LOGGER.error(err)


@dp.callback_query_handler(text_contains='wa_mailing:mailing_correct:', state=ClientState.client)
async def WA_mailing_correct(call: types.CallbackQuery):
    try:
        mai_id = call.data.split(':')[-1]
        wa_repo = get_wa_client_repo()
        mai = await wa_repo.get_mailing_by_id(mai_id)
        await call.message.edit_reply_markup(reply_markup=get_inline_wa_mailing_correct_markup(mai))
    except Exception as err:
        LOGGER.error(err)


@dp.callback_query_handler(text_contains='wa_mailing:mailing_correct_text:', state=ClientState.client)
async def WA_mailing_correct_text(call: types.CallbackQuery, state: FSMContext):
    try:
        mai_id = call.data.split(':')[-1]
        await call.message.answer('Введите новый текст для рассылки')
        async with state.proxy() as data:
            data['mai_id'] = mai_id
        await GlobalState.wa_mailing_cor_text.set()
    except Exception as er:
        LOGGER.error(er)


@dp.message_handler(state=GlobalState.wa_mailing_cor_text)
async def WA_mailing_correct_text_save(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            mai_id = data['mai_id']
        wa_repo = get_wa_client_repo()
        await wa_repo.mailing_update(
             mai_id, text=message.text
        )
        await ClientState.client.set()
        await message.answer('Рассылка успешно обновлена', reply_markup=MAIN_CL_MARKUP)
    except Exception as err:
        LOGGER.error(err)
        await GlobalState.admin.set()
        await message.answer(f'Что-то пошло не так, попробуйте позже\n\n{err}', reply_markup=MAIN_CL_MARKUP)

@dp.callback_query_handler(text_contains='wa_mailing:mailing_correct_ph:', state=ClientState.client)
async def WA_mailing_correct_phones(call: types.CallbackQuery, state: FSMContext):
    try:
        mai_id = call.data.split(':')[-1]
        async with state.proxy() as data:
            data['m_id'] = mai_id
        wa_repo = get_wa_client_repo()
        mai = await wa_repo.get_mailing_by_id(mai_id)
        await call.message.answer(
            'Пришилите файл в формате "xlsx", столбец с номерами телефонов должен называться "phone"',
            reply_markup=cancel_markup()
        )
        await GlobalState.wa_mailing_correct_file.set()
    except Exception as err:
        LOGGER.error(err)

@dp.message_handler(content_types=[types.ContentType.DOCUMENT, ], state=GlobalState.wa_mailing_correct_file)
async def WA_correct_phones_info(message: types.Message, state: FSMContext):
    try:
        file = await bot.get_file(message.document.file_id)
        file_path = file.file_path
        await bot.download_file(file_path, f"./wa_mailing_contacts/wa_{message.from_user.id}.xlsx")
        phones, count_phones = await WA_xlsx_search('phone', message.from_user.id)
        async with state.proxy() as data:
            data['phones'], data['count_phones'] = phones, count_phones
        path = os.path.join(
                os.path.abspath(os.path.dirname(__file__)), f'./wa_mailing_contacts/wa_{message.chat.id}.xlsx'
        )
        os.remove(path)
        async with state.proxy() as data:
            await message.answer(f'Найдено {count_phones} номеров для рассылки', reply_markup=wa_save_correct_phones_markup(data['m_id']))
    except Exception as err:
        LOGGER.error(err)

@dp.callback_query_handler(text_contains='wa_client:save_correct_phones:', state=GlobalState.wa_mailing_correct_file)
async def WA_mailing_correct_phones_save(call: types.CallbackQuery, state: FSMContext):
    mai_id = int(call.data.split(':')[-1])
    try:
        async with state.proxy() as data:
            for_sending = int(data['count_phones'])
            phones = data['phones']
        wa_repo = get_wa_client_repo()
        await wa_repo.update_mailing_contacts(
             mai_id, for_sending, phones
        )
        await ClientState.client.set()
        await call.message.edit_reply_markup(reply_markup=None)
        await call.message.answer('Рассылка успешно обновлена', reply_markup=MAIN_CL_MARKUP)
    except Exception as err:
        LOGGER.error(err)
        await GlobalState.admin.set()
        await call.message.answer(f'Что-то пошло не так, попробуйте позже\n\n{err}', reply_markup=MAIN_CL_MARKUP)

@dp.message_handler(state=None)
async def to_main_if_reboot(message: types.Message, state: FSMContext):
    user_repo = get_user_repo()
    user = await user_repo.get_by_id(message.from_user.id)
    cur_state = await state.get_state()
    if user:
        if cur_state is None:
            await message.answer('Произошла перезагрузка системы')
            if user.role_id == 10:
                await message.answer('Вы в главном меню', reply_markup=MAIN_CL_MARKUP)
                await GlobalState.admin.set()
            elif user.role_id == 2:
                await message.answer('Вы в главном меню', reply_markup=MAIN_CL_MARKUP)
                await ClientState.client.set()
    else:
        await message.answer('Для начала регистрации - нажмите /start')

async def on_shutdown(dp):
    """Отключаемся от БД при выключении бота."""
    try:
        await database.disconnect()
        LOGGER.info('DB disconnected')
    except Exception as err:
        LOGGER.error(err)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)
