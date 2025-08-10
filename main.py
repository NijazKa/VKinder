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


def sender(user_id, text): # функция отправки сообщения от бота к пользователю + клавиатура
    vk.messages.send(user_id=user_id, message=text, random_id=randrange(10 ** 7), keyboard=keyboard.get_keyboard())

# функция получения трех фотографий пользователя с наибольшим количеством лайков
def top_photo(user_id):
    albums = vk.photos.getAlbums(owner_id=user_id)
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


### БАЗОВЫЙ ЦИКЛ ЗАПУСКА БОТА
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
