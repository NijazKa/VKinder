import json
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from random import randrange

from config import TOKEN

# Блок авторизации
vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)
# Блок авторизации

# def write_msg(user_id, message):
#     vk.method('messages.send', {'user_id': user_id, 'message': message,  'random_id': randrange(10 ** 7),})

# Создание клавиатуры
keyboard = VkKeyboard(one_time=True)
keyboard.add_button('Вперед', color=VkKeyboardColor.SECONDARY)
keyboard.add_button('Назад', color=VkKeyboardColor.POSITIVE)
keyboard.add_button('В избранное', color=VkKeyboardColor.POSITIVE)


def sender(id, text): # функция отправки сообщения от бота к пользователю
    vk.messages.send(user_id=id, message=text, random_id=randrange(10 ** 7), keyboard=keyboard.get_keyboard())

for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW:
        if event.to_me:
            request = event.text.lower()
            if request == "привет":
                sender(event.user_id, f"Хай, {event.user_id}")
            elif request == "пока":
                sender(event.user_id, "Пока((")
            else:
                sender(event.user_id, "Не поняла вашего ответа...")