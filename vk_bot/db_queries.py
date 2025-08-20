from datetime import datetime
from sqlalchemy.orm import joinedload
from vk_bot.database import SessionLocal
from vk_bot.models import User, UserInteraction, Candidate, Photo
from .keyboards import keyboard
from .vk_logic import top_photo

def new_user(user_id, vk):
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


def user_search(user_vk_id, vk_user, vk):
    ''' Функция поиска пользователей по параметрам user_search
    - id - integer Идентификатор пользователя.
    - is_closed - boolean Скрыт ли профиль пользователя настройками приватности.
    - has_photo - integer Информация о том, установил ли пользователь фотографию для профиля. Возвращаемые значения: 1 — установил, 0 — не установил.
'''
    ses = SessionLocal()
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
            get_photos = top_photo(candidate_vk_id, vk_user)
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

def like_candidate(user_id,vk):
    ses = SessionLocal()
    current_user = ses.query(User).filter_by(vk_id=user_id).first()
    last_interaction = ses.query(UserInteraction).filter(UserInteraction.user_id == current_user.user_id).order_by(UserInteraction.created_at.desc()).first()
    last_interaction.status = 'liked'
    ses.commit()
    text = 'Отлично! Анкета сохранена. Как только захочешь просмотреть понравившиеся анкеты - нажми Избранное'
    vk.messages.send(user_id=user_id, message=text, random_id=0, keyboard=keyboard.get_keyboard())
    ses.commit()

def favourite_users(user_id, vk): #выдача списка избранных кандидатов
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
    vk.messages.send(user_id=user_id, message=sending_text, random_id=0, keyboard=keyboard.get_keyboard())
    for profile in liked_candidates:
        text = f"{profile.first_name} {profile.last_name}\n{profile.profile_url}"
        first_photo = profile.photos[0]
        attachment_str = first_photo.attachment
        vk.messages.send(user_id=user_id, message=text, attachment=attachment_str, random_id=0)
    ses.close()
