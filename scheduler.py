from wapp.wa_api import wa_check_state, wa_get_acc_settings
from enums import WA_CStatuses
from repositories.getRepo import get_user_repo, get_wa_client_repo
from bot import LOGGER, bot, scheduler

async def check_WA_accs():
    count_logout, count_auth, count_ban = 0, 0, 0
    try:
        user_repo = get_user_repo()
        admins = await user_repo.get_all_admins()
        wa_repo = get_wa_client_repo()
        all_accs = await wa_repo.get_all()
        LOGGER.info('Начинается ежедневная проверка авторизации всех аккаутов WA')
        for acc in all_accs:
            wa_acc_state = await wa_check_state(acc)
            LOGGER.info(f'Состояние интсанса {acc.id}: {wa_acc_state}')
            if wa_acc_state == 'authorized':
                phone = await wa_get_acc_settings(acc)
                await wa_repo.update(acc.id, phone = phone['wid'], status_id=WA_CStatuses.AUTHORIZED.value['id'])
                count_auth+=1
            elif wa_acc_state == 'notAuthorized' and acc.status_id == WA_CStatuses.AUTHORIZED.value['id']:
                await wa_repo.update(
                        acc.id, phone = 'not authorized',
                        status_id=WA_CStatuses.WAITING_AUTHORIZATION.value['id']
                    )
                for admin in admins:
                    await bot.send_message(chat_id=admin.id, text=f'Инстанс #{acc.id} не авторизован, авторизуйте инстанс')
                count_logout+=1
            elif wa_acc_state == 'blocked' and acc.status_id == WA_CStatuses.AUTHORIZED.value['id']:
                await wa_repo.update(acc.id, phone = 'not authorized', status_id=WA_CStatuses.BANNED.value['id'])
                for admin in admins:
                    await bot.send_message(chat_id=admin.id, text=f'Аккаунт #{acc.id} заблокирован, требуется авторизовать новый аккаунт')
                count_ban += 1
            else:
                LOGGER.debug(f'Непонятный статус акка: {acc.id}')
        ser_mes = (
            'Отчет акков WA:\n\n'
            f'Всего акков: {len(all_accs)}\n'
            f'Кол-во авторизованных акков: {count_auth}\n'
            f'Кол-во забаненых акков: {count_ban}\n'
            f'Кол-во разлогинившихся акков акков: {count_logout}\n'
        )
        for admin in admins:
            await bot.send_message(chat_id=admin.id, text=ser_mes)
    except Exception as er:
        LOGGER.error(f'Ошибка ежедневной проверки акков WA: {er}')


scheduler.add_job(check_WA_accs, 'cron', day_of_week='mon-sun', hour=7, minute=30)