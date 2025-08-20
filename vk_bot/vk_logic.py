import random
from vk_bot.keyboards import keyboard


def first_sender(user_id, text, vk): # функция отправки первого сообщения от бота к пользователю
    vk.messages.send(user_id=user_id, message=text, random_id=random.randrange(10 ** 7))

def main_sender(user_id, text, vk): # функция отправки сообщения от бота к пользователю + клавиатура
    vk.messages.send(user_id=user_id, message=text, random_id=random.randrange(10 ** 7), keyboard=keyboard.get_keyboard())

# функция получения трех фотографий пользователя с наибольшим количеством лайков
def top_photo(user_id, vk_user):
    photos = vk_user.photos.get(owner_id=user_id, 
                                album_id='profile',  
                                extended=1,
                                count=100)
    if not photos.get('items'):
            return []
    top_photos = sorted(photos['items'], key=lambda x: x['likes']['count'], reverse=True)[:3]
    result= []
    for photo in top_photos:
        result.append({'owner_id': photo['owner_id'],
                       'photo_id': photo['id'],
                       'likes': photo['likes']['count'],
                       'attachment': f"photo{photo['owner_id']}_{photo['id']}"})
    return result
