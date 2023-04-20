import enum


class URoles(enum.Enum):
    """ `User` roles `value = {'id':id, 'name':name}`"""
    ADMIN = {'id': 10, 'name': 'admin'}
    PENDING = {'id': 5, 'name': 'pending'}
    USER = {'id': 2, 'name': 'user'}


class WA_CWorkes(enum.Enum):
    """ `Client` workes `value = {'id':id, 'name':name, 'answer':answer}` """
    UNWORKING = {'id': 1, 'name': 'unworking', 'answer': 'Свободен'}
    CHECKING = {'id': 2, 'name': 'checking', 'answer': 'Проверяет аккаунты'}
    MAILING = {'id': 3, 'name': 'mailing', 'answer': 'Участвует в рассылке'}

    @classmethod
    def _missing_(cls, id):
        for work in cls:
            if work.value['id'] == id:
                return work
        return None


class WA_CStatuses(enum.Enum):
    """ `Client` statuses `value = {'id':id, 'name':name, 'answer':answer, 'sticker': stiker}` """
    AUTHORIZED = {'id': 1, 'name': 'authorized', 'answer': 'Авторизован', 'sticker': '🟢'}
    WAITING_AUTHORIZATION = {'id': 2, 'name': 'waiting_for_authorization', 'answer': 'Требуется авторизация', 'sticker': '🟡'}
    BANNED = {'id': 3, 'name': 'banned', 'answer': 'Аккаунт забанен', 'sticker': '🔴'}

    @classmethod
    def _missing_(cls, id):
        for status in cls:
            if status.value['id'] == id:
                return status
        return None

class WA_Mailing_statuses(enum.Enum):
    """ `Client` statuses `value = {'id':id, 'name':name, 'answer':answer, 'sticker': stiker}` """
    
    UNWORKING = {'id': 1, 'name': 'unworking', 'answer': 'не запущена'}
    WORKING = {'id': 2, 'name': 'working', 'answer': 'в процессе'}
    FINISHED = {'id': 3, 'name': 'finished', 'answer': 'завершена'}
    PAUSED = {'id': 4, 'name': 'paused', 'answer': 'на паузе'}

    @classmethod
    def _missing_(cls, id):
        for status in cls:
            if status.value['id'] == id:
                return status
        return None