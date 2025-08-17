import json
from dataclasses import fields
from datetime import datetime

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import random
import pprint
from database import SessionLocal
from models import User, UserInteraction, Candidate, Photo
from config import TOKEN, USER_TOKEN

# Блок авторизации группы
vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)

# Блок авторизации пользователя для парсера
vk_user_session = vk_api.VkApi(token=USER_TOKEN)
vk_user = vk_user_session.get_api()

# Создание клавиатуры
keyboard = VkKeyboard(one_time=True)
keyboard.add_button('Назад', color=VkKeyboardColor.SECONDARY)
keyboard.add_button('Лайк', color=VkKeyboardColor.POSITIVE) #
keyboard.add_button('Вперед', color=VkKeyboardColor.SECONDARY)
keyboard.add_button('Избранное', color=VkKeyboardColor.PRIMARY)
keyboard.add_button('Справка', color=VkKeyboardColor.PRIMARY)


def first_sender(user_id, text): # функция отправки первого сообщения от бота к пользователю
    vk.messages.send(user_id=user_id, message=text, random_id=random.randrange(10 ** 7))

def main_sender(user_id, text): # функция отправки сообщения от бота к пользователю + клавиатура
    vk.messages.send(user_id=user_id, message=text, random_id=random.randrange(10 ** 7), keyboard=keyboard.get_keyboard())

# функция получения трех фотографий пользователя с наибольшим количеством лайков
def top_photo(user_id):
    albums = vk_user.photos.getAlbums(owner_id=user_id)
    all_photos = vk_user.photos.getAll(owner_id=user_id,extended=1)

    photos = []
    # Проходим по каждому альбому и получаем фотографии
    for photo in all_photos['items']:
        photos.append({
                        'url': photo['orig_photo']['url'],
                        'likes': photo['likes']['count']
                    })

    # Сортируем фотографии по количеству лайков и выбираем три с наибольшим количеством
    top_photos = sorted(photos, key=lambda x: x['likes'], reverse=True)[:3]

    three_photos = ''
    num = 0
    # Выводим найденные фотографии
    for photo in top_photos:
        num += 1
        print(f"URL: {photo['url']}, Likes: {photo['likes']}") #пока печать, потом записать в базу данных
        three_photos += str(num) + '. ' + photo['url'] + '\n'
    return three_photos

# функция получения данных о новом пользователе, после запуска бота, сюда же прописать работу с БД
def new_user(user_id):
    user = vk.users.get(user_ids=user_id, fields='sex, home_town, bdate, is_closed, has_photo')
    user_data = user[0]
    ses = SessionLocal()
    key1 = 'home_town'
    vk_id = user[0]['id']
    last_updated_info = datetime.today()
    try:
        birth_date = datetime.strptime(user_data.get('bdate'), "%d.%m.%Y")
        today = datetime.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    except:
        text = 'Не удалось получить вашу дату рождения :( Заполните дату на старнице в формате ДД.ММ.ГГГГ и возвращайтесь'
        vk.messages.send(user_id=user_id, message=text)
    user_from_db = ses.query(User).filter_by(vk_id=vk_id).first()
    if user_from_db is None:
        if key1 in user[0] and user[0]['is_closed'] == False:
            assoc = User(vk_id=vk_id,
                         first_name=user_data.get('first_name'),
                         second_name=user_data.get('last_name'),
                         user_sex=user_data.get('sex'),
                         city=user_data.get('home_town'),
                         user_age=age,
                         last_updated_info=last_updated_info)
            ses.add(assoc)
            ses.commit()
            ses.close()
        elif user[0]['is_closed'] == True:
            text = 'Твой профиль закрыт, не смогу найти вторую половинку, т.к. не вижу твоих параметров. Открой сво профиль и продолжим :)'
            vk.messages.send(user_id=user_id, message=text)
        elif key1 not in user[0] and user[0]['is_closed'] == False:
            text = 'Добавь город у себя на странице и возвращайся. Без этого не сможем продолжить поиск второй половинки'
            vk.messages.send(user_id=user_id, message=text)
        # else:
        #     print('надо выполнить все условия')
        # print(user[0])
        # return user[0] # на выходе словарь вида {'id': 175072795, 'bdate': '18.4.2007', 'home_town': 'Москва', 'sex': 2, 'first_name': 'Нияз', 'last_name': 'Нияз', 'can_access_closed': True, 'is_closed': False}


''' функция поиска пользователей по параметрам user_search
id - integer Идентификатор пользователя.

is_closed - boolean Скрыт ли профиль пользователя настройками приватности.
    
can_access_closed - boolean Может ли текущий пользователь видеть профиль при is_closed = 1 (например, он есть в друзьях).

bdate - string Дата рождения. Возвращается в формате D.M.YYYY или D.M (если год рождения скрыт). Если дата рождения скрыта целиком, поле отсутствует в ответе.

has_photo - integer Информация о том, установил ли пользователь фотографию для профиля. Возвращаемые значения: 1 — установил, 0 — не установил.
'''
def user_search(city, sex, age):
    # Параметры поиска
    params = {
        'is_closed': False,
        'sort': 0, # сортировка по популярности
        'has_photo': 1, # искать только с фото
        'hometown': city,  # название города
        'age': age,  # соотв. возрасту пользователя
        'sex': sex,  # Пол (1 - женский, 2 - мужской)
        'count': 50  # Количество результатов
    }

    # Выполнение поиска
    users = vk_user.users.search(**params)
    ses = SessionLocal()
    user_vk_id = event.user_id
    # i = random.randint(0, len(users['items']) - 1) # рандомная выдача пользователя
    current_user = ses.query(User).filter_by(vk_id=user_vk_id).first()
    for data in users['items']:
        candidate_vk_id = data['id']
        existing_candidate = ses.query(Candidate).filter_by(vk_id=candidate_vk_id).first()
        if existing_candidate:
            get_status = ses.query(UserInteraction.status)\
                        .join(Candidate)\
                        .filter(
                            UserInteraction.user_id == current_user.user_id,
                            Candidate.vk_id == candidate_vk_id
                        ).first()
            if get_status is not None:
                get_photos = top_photo(candidate_vk_id)
                first_name = data.get('first_name', '')
                last_name = data.get('last_name', '')
                profile_url = f"https://vk.com/id{candidate_vk_id}"
                text = f"{first_name} {last_name}\n{profile_url}\n{get_photos}"
                vk.messages.send(user_id=user_vk_id, message=text)

def like_candidate(user_id):
    #if event.text.lower() == 'лайк':
    """Здесь должна быть логика прописанная на событие "лайк", надо добавить память боту"""
    ses = SessionLocal()
    user_id = event.user_id      
    new_candidate = Candidate(vk_id=candidate_vk_id,
                            first_name=first_name,
                            last_name=last_name,
                            profile_url=profile_url)
    action = UserInteraction(
        user_id=current_user.user_id,
        candidate_id=candidate.candidate_id,
        status='liked')
    ses.add(new_candidate)
    ses.commit()
    ses.add(action)
    ses.commit()
        
    # return f'Ссылка на профиль https://vk.com/id{users['items'][i]['id']} \nИмя: {users['items'][i]['first_name']} {users['items'][i]['last_name']} \n{top_photo(users['items'][i]['id'])}'

'''функция вызывается после нажатия кнопки Вперед
парсим данные о пользователях через функцию user_search
не знаю надо ли выносить это в отдельную функцию
'''
def next_user():
    user_search()
    pass

'''Функция установки лайка пользователю
Добавляет id пользователя в базу данных и присваивает ему параметр 1 (0 у просмотренных пользователей) 
'''
def like(user_id):
    # получить id последнего просмотренного пользователя из БД и поменять у него параметр
    pass

def previous_user(user_id):
    # получить из таблицы -2 добавленного пользователя и вывести данные по нему в бота
    pass


# ### БАЗОВЫЙ ЦИКЛ ЗАПУСКА БОТА
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        user_id = event.user_id
        request = event.text.lower()
        if request == "привет" or request == "/start":
            new_user(user_id)
            main_sender(event.user_id, f"Хай, для старта нажми кнопку Вперед")
            new_user(event.user_id)
        elif request == "начать":
            main_sender(event.user_id, f"Хай, для старта нажми кнопку Вперед")

        elif request == "вперед":
            main_sender(event.user_id, f"{user_search()}")

        elif request == "лайк":
            pass
        elif request == "назад":
            pass
        elif request == "избранное":
            pass
        elif request == "справка":
            pass
        else:
            main_sender(event.user_id, f"Не поняла вашей команды")


#top_photo(208471155)
#new_user(196463845)

#user_search()

# 1
