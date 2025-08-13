import json
from dataclasses import fields

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from random import randrange

from config_main import TOKEN, USER_TOKEN

# Блок авторизации группы
vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)

# Блок авторизации пользователя для парсера
vk_user_session = vk_api.VkApi(token=USER_TOKEN)
vk_user = vk_user_session.get_api()

# def write_msg(user_id, message):
#     vk.method('messages.send', {'user_id': user_id, 'message': message,  'random_id': randrange(10 ** 7),})

# Создание клавиатуры
keyboard = VkKeyboard(one_time=True)
keyboard.add_button('Назад', color=VkKeyboardColor.SECONDARY)
keyboard.add_button('Лайк', color=VkKeyboardColor.POSITIVE) #
keyboard.add_button('Вперед', color=VkKeyboardColor.SECONDARY)
keyboard.add_button('Избранное', color=VkKeyboardColor.PRIMARY)
keyboard.add_button('Справка', color=VkKeyboardColor.PRIMARY)


def first_sender(user_id, text): # функция отправки сообщения от бота к пользователю + клавиатура
    vk.messages.send(user_id=user_id, message=text, random_id=randrange(10 ** 7), keyboard=keyboard.get_keyboard())

def main_sender(user_id, text): # функция отправки сообщения от бота к пользователю + клавиатура
    vk.messages.send(user_id=user_id, message=text, random_id=randrange(10 ** 7), keyboard=keyboard.get_keyboard())

# функция получения трех фотографий пользователя с наибольшим количеством лайков
def top_photo(user_id):
    albums = vk_user.photos.getAlbums(owner_id=user_id)
    photos = []
    # Проходим по каждому альбому и получаем фотографии
    for album in albums['items']:
        album_id = album['id']
        # Получаем фотографии из альбома
        photos_in_album = vk.photos.get(owner_id=user_id, album_id=album_id, count=1000)
        for photo in photos_in_album['items']:
            # Добавляем фотографию и количество лайков в список
            photos.append({
                'url': photo['sizes'][-1]['url'],
                'likes': photo['likes']['count']
            })

    # Сортируем фотографии по количеству лайков и выбираем три с наибольшим количеством
    top_photos = sorted(photos, key=lambda x: x['likes'], reverse=True)[:3]

    # Выводим найденные фотографии
    for photo in top_photos:
        print(f"URL: {photo['url']}, Likes: {photo['likes']}") #пока печать, потом записать в базу данных

# функция получения данных о новом пользователе, после запуска бота, сюда же прописать работу с БД
def new_user(user_id):
    user = vk.users.get(user_ids=user_id, fields='sex, home_town, bdate')
    return user[0] # на выходе словарь вида {'id': 175072795, 'bdate': '18.4.2007', 'home_town': 'Москва', 'sex': 2, 'first_name': 'Нияз', 'last_name': 'Нияз', 'can_access_closed': True, 'is_closed': False}

# функция поиска пользователей по параметрам
def user_search():
    # Параметры поиска
    params = {
        'q': '',  # Поисковый запрос (опционально)
        'city': 1,  # ID города (1 - Москва, 2 - Санкт-Петербург)
        'age_from': 18,  # Минимальный возраст
        'age_to': 25,  # Максимальный возраст
        'sex': 1,  # Пол (1 - женский, 2 - мужской)
        'count': 100  # Количество результатов
    }

    # Выполнение поиска
    users = vk_user.users.search(**params)

    # Обработка результатов
    for user in users['items']:
        print(f"ID: {user['id']}")
        print(f"Имя: {user['first_name']} {user['last_name']}")
        print(f"Город: {user.get('city', {}).get('title', 'Не указан')}")
        print(f"Возраст: {user.get('bdate', 'Не указан')}")
        print("-" * 30)


# ### БАЗОВЫЙ ЦИКЛ ЗАПУСКА БОТА
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        request = event.text.lower()
        if request == "привет" or request == "/start":
            main_sender(event.user_id, f"Хай, {event.user_id}")
            new_user(event.user_id)





