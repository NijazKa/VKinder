from dataclasses import fields
from datetime import datetime
from sqlalchemy.orm import joinedload

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import random
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
keyboard.add_button('Лайк', color=VkKeyboardColor.POSITIVE) 
keyboard.add_button('Вперед', color=VkKeyboardColor.SECONDARY)
keyboard.add_button('Избранное', color=VkKeyboardColor.PRIMARY)
keyboard.add_button('Справка', color=VkKeyboardColor.PRIMARY)


def first_sender(user_id, text): # функция отправки первого сообщения от бота к пользователю
    vk.messages.send(user_id=user_id, message=text, random_id=random.randrange(10 ** 7))

def main_sender(user_id, text): # функция отправки сообщения от бота к пользователю + клавиатура
    vk.messages.send(user_id=user_id, message=text, random_id=random.randrange(10 ** 7), keyboard=keyboard.get_keyboard())

# функция получения трех фотографий пользователя с наибольшим количеством лайков
def top_photo(user_id):
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

# Функция получения данных о новом пользователе, после запуска бота
def new_user(user_id):
    user = vk.users.get(user_ids=user_id, fields='sex, city, bdate, is_closed, has_photo')
    user_data = user[0]
    vk_id = user[0]['id']
    ses = SessionLocal()
    if user[0]['is_closed'] == True:
        text = 'Твой профиль закрыт, не смогу найти вторую половинку, т.к. не вижу твоих параметров. Открой сво профиль и продолжим :)'
        vk.messages.send(user_id=user_id, message=text, random_id=0)
        return
    last_updated_info = datetime.today()
    try:
        birth_date = datetime.strptime(user_data.get('bdate'), "%d.%m.%Y")
        today = datetime.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    except:
        text = 'Не удалось получить вашу дату рождения :( Заполните дату на старнице в формате ДД.ММ.ГГГГ и возвращайтесь'
        vk.messages.send(user_id=user_id, message=text, random_id=0)
        return
    city_data = user_data.get('city')
    if not city_data:
        text = 'Добавь город у себя на странице и возвращайся. Без этого не сможем продолжить поиск второй половинки'
        vk.messages.send(user_id=user_id, message=text, random_id=0)
        return
    user_from_db = ses.query(User).filter_by(vk_id=vk_id).first()
    if user_from_db is None:
        assoc = User(vk_id=vk_id,
                    first_name=user_data.get('first_name'),
                    second_name=user_data.get('last_name'),
                    user_sex=user_data.get('sex'),
                    city=city_data.get('id'),
                    user_age=age,
                    last_updated_info=last_updated_info)
        ses.add(assoc)
        ses.commit()
        
    else:
        user_from_db.first_name = user_data.get('first_name')
        user_from_db.second_name = user_data.get('last_name')
        user_from_db.user_sex = user_data.get('sex')
        user_from_db.city = city_data.get('id')
        user_from_db.user_age = age
        user_from_db.last_updated_info = last_updated_info
        ses.commit()
    ses.close()


def user_search(user_vk_id):
    ''' Функция поиска пользователей по параметрам user_search
    - id - integer Идентификатор пользователя.
    - is_closed - boolean Скрыт ли профиль пользователя настройками приватности.
    - has_photo - integer Информация о том, установил ли пользователь фотографию для профиля. Возвращаемые значения: 1 — установил, 0 — не установил.
'''
    ses = SessionLocal()
    user_vk_id = event.user_id
    current_user = ses.query(User).filter_by(vk_id=user_vk_id).first()
    city = current_user.city
    age = current_user.user_age
    sex_user = current_user.user_sex
    if sex_user == 1:
        sex = 2
    else:
        sex = 1
    # Параметры поиска
    params = {
        'is_closed': False,
        # 'sort': 0, # сортировка по популярности
        'has_photo': 1, # искать только с фото
        'city': city,  # название города
        'age_from': age - 2,
        'age_to': age + 2,
        'sex': sex,  # Пол (1 - женский, 2 - мужской)
        'count': 1000,  # Количество результатов
        'status': 6
    }
    # Выполнение поиска
    users = vk_user.users.search(**params)
    current_user = ses.query(User).filter_by(vk_id=user_vk_id).first()
    for data in users['items']:
        candidate_vk_id = data['id']
        get_status = ses.query(UserInteraction.status)\
                    .join(Candidate)\
                    .filter(
                        UserInteraction.user_id == current_user.user_id,
                        Candidate.vk_id == candidate_vk_id
                    ).first()
        if get_status is None:
            get_photos = top_photo(candidate_vk_id)
            attachments = [photo['attachment'] for photo in get_photos]
            attachment_str = ",".join(attachments)
            first_name = data.get('first_name', '')
            last_name = data.get('last_name', '')
            profile_url = f"https://vk.com/id{candidate_vk_id}"
            text = f"{first_name} {last_name}\nСсылка на профиль: {profile_url}\n"
            vk.messages.send(user_id=user_vk_id, message=text, attachment=attachment_str, random_id=0, keyboard=keyboard.get_keyboard())
            assoc = Candidate(vk_id=candidate_vk_id,
                                first_name=first_name,
                                last_name=last_name,
                                profile_url=profile_url)
            ses.add(assoc)
            ses.flush() 
            assoc2 = UserInteraction(user_id=current_user.user_id,
                                        candidate_id=assoc.candidate_id,
                                        status='seen'
                                        )
            ses.add(assoc2)
            for photo in get_photos:
                new_photo = Photo(candidate_id=assoc.candidate_id, 
                                  owner_id=photo['owner_id'],
                                  count_likes=photo['likes'],
                                  attachment=photo['attachment'])
                ses.add(new_photo)
                break
    ses.commit()
    ses.close()

def like_candidate(user_id):
    user_id = event.user_id
    ses = SessionLocal()
    current_user = ses.query(User).filter_by(vk_id=user_id).first()
    last_interaction = ses.query(UserInteraction).filter(UserInteraction.user_id == current_user.user_id).order_by(UserInteraction.created_at.desc()).first()
    last_interaction.status = 'liked'
    ses.commit()
    text = 'Отлично! Анкета сохранена. Как только захочешь просмотреть понравившиеся анкеты - нажми Избранное'
    vk.messages.send(user_id=user_id, message=text, random_id=0, keyboard=keyboard.get_keyboard())
    ses.commit()

def favourites_users(user_id): #выдача списка избранных кандидатов
    user_id = event.user_id
    ses = SessionLocal()
    liked_candidates = ses.query(Candidate)\
            .join(UserInteraction)\
            .join(User)\
            .options(joinedload(Candidate.photos))\
            .filter(User.vk_id == user_id,
                    UserInteraction.status == 'liked').all()
    if not liked_candidates:
            vk.messages.send(user_id=user_id, message="Ваш список избранного пуст. Нажми Лайк на, если понравилась анкета", random_id=0)
            return
    sending_text = 'Отправляю список сохраненных анкет...'
    vk.messages.send(user_id=user_id, message=sending_text, random_id=0)
    for profile in liked_candidates:
        text = f"{profile.first_name} {profile.last_name}\n{profile.profile_url}"
        first_photo = profile.photos[0]
        attachment_str = first_photo.attachment
        vk.messages.send(user_id=user_id, message=text, attachment=attachment_str, random_id=0)
    ses.close()

# ### БАЗОВЫЙ ЦИКЛ ЗАПУСКА БОТА
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        user_id = event.user_id
        request = event.text.lower()
        if request == 'привет' or request == '/start': 
            #new_user(user_id)
            main_sender(event.user_id, f"Хай, для старта нажми кнопку Вперед")
            new_user(event.user_id)
        elif request == "вперед":
            user_search(event.user_id) 
        elif request == "лайк":
            like_candidate(event.user_id)
        elif request == "избранное":
            new_user(user_id)
        elif request == "справка":
            main_sender(event.user_id, f'Добро пожаловать в умного бота VK\nДля работы с ботом Вам\
                        необходимо получить TOKEN на странице https://vkhost.github.io/ \nПосле этого\
                        Вам будут предлагаться пользователи, с которыми вы можете познакомиться')
        else:
            main_sender(event.user_id, f"Не поняла вашей команды")


