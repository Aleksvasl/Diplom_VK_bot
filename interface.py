# импорты
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
import re
from datetime import datetime
from config import comunity_token, acces_token
from core import VkTools

from data_store import engine, user_add, user_check
# отправка сообщений


class BotInterface():
    def __init__(self, comunity_token, acces_token):
        self.vk = vk_api.VkApi(token=comunity_token)
        self.longpoll = VkLongPoll(self.vk)
        self.vk_tools = VkTools(acces_token)
        self.params = {}
        self.worksheets = []
        self.keys = []
        self.offset = 0

    def message_send(self, user_id, message, attachment=None):
        self.vk.method('messages.send',
                       {'user_id': user_id,
                        'message': message,
                        'attachment': attachment,
                        'random_id': get_random_id()}
                       )

    def _bdate_toyear(self, bdate):
        user_year = bdate.split('.')[2]
        now = datetime.now().year
        return now - int(user_year)

    def photos_for_send(self, worksheet):
        photos = self.vk_tools.get_photos(worksheet['id'])
        photo_string = ''
        for photo in photos:
            photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'

        return photo_string

    def send_mes_exc(self, event):
        if self.params['name'] is None:
            self.message_send(event.user_id, 'Введите ваше имя и фамилию:')
            for event in self.longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    return event.text

        elif self.params['sex'] is None:
            self.message_send(event.user_id, 'Введите свой пол (1-м, 2-ж):')
            for event in self.longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    return int(event.text)

        elif self.params['city'] is None:
            self.message_send(event.user_id, 'Введите город:')
            for event in self.longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    return event.text

        elif self.params['year'] is None:
            self.message_send(event.user_id, 'Введите дату рождения (дд.мм.гггг):')
            for event in self.longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    return self._bdate_toyear(event.text)

# обработка событий / получение сообщений
    def event_handler(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text.lower() == 'привет':
                    '''Логика для получения данных о пользователе'''
                    self.params = self.vk_tools.get_profile_info(event.user_id)
                    self.message_send(
                        event.user_id, f'Привет друг, {self.params["name"]}')

                    # Недостающие данные
                    self.keys = self.params.keys()
                    for i in self.keys:
                        if self.params[i] is None:
                            self.params[i] = self.send_mes_exc(event)

                    self.message_send(event.user_id, 'Вы успешно зарегистрировались!')

                elif event.text.lower() == 'поиск':
                    '''Логика для поиска анкет'''
                    self.message_send(
                        event.user_id, 'Поиск...')
                    while True:
                        if self.worksheets:
                            worksheet = self.worksheets.pop()
                            # здесь логика дял проверки и добавления в бд
                            if user_check(engine, event.user_id, worksheet['id']) is False:
                                user_add(engine, event.user_id, worksheet['id'])
                                break
                        else:
                            self.worksheets = self.vk_tools.search_worksheet(self.params, self.offset)

                    photo_string = self.photos_for_send(worksheet)
                    self.offset += 10

                    self.message_send(
                        event.user_id,
                        f'Имя: {worksheet["name"]} ссылка: vk.com/id{worksheet["id"]}',
                        attachment=photo_string
                    )

                elif event.text.lower() == 'пока':
                    self.message_send(
                        event.user_id, 'До новых встреч!')
                else:
                    self.message_send(
                        event.user_id, 'Ошибка: введена несуществующая команда')


if __name__ == '__main__':
    bot_interface = BotInterface(comunity_token, acces_token)
    bot_interface.event_handler()
