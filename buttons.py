from enum import Enum

class Bts(Enum):
    """ Надписи на кнопках """
    MAILINGS = 'Мои рассылки'
    ACCS = 'Мои аккаунты'
    TARIF = 'Мой тариф'
    SUP = 'Моя поддержка'
    NEW_MAILING = 'Создать рассылку'
    GO_TO_MAIN = '◀️На главную'


class ClientBts(Enum):
    """ Надписи на кнопках для клиента"""
    ACCEPT_POLICY = 'Принять и продолжить'
    SEARCH_OP_CHATS = 'Поиск источников(чатов)'
    SET_UP_INVITE = 'Настроить инвайт'
    SEARCH_HISTORY = 'История поиска'
    QUE_AND_ANS = 'Вопросы и ответы'
    PROFILE = 'Профиль'
    REPLENISH_BALANCE = 'Пополнить баланс'