import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType

from config import TOKEN, USER_TOKEN
from vk_bot.vk_logic import main_sender
from vk_bot.db_queries import new_user, user_search, like_candidate, favourite_users
from vk_bot.vk_logic import main_sender


# Блок авторизации группы
vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)

# Блок авторизации пользователя для парсера
vk_user_session = vk_api.VkApi(token=USER_TOKEN)
vk_user = vk_user_session.get_api()


# ### БАЗОВЫЙ ЦИКЛ ЗАПУСКА БОТА
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        user_id = event.user_id
        request = event.text.lower()
        if request == "привет" or request == "/start":
            # new_user(user_id)
            main_sender(event.user_id, f"Хай, для старта нажми кнопку Вперед", vk)
            new_user(event.user_id, vk)
        elif request == "вперед":
            user_search(event.user_id, vk_user, vk)
        elif request == "лайк":
            like_candidate(event.user_id, vk)
        elif request == "избранное":
            favourite_users(user_id, vk)
        elif request == "справка":
            main_sender(
                event.user_id,
                f"Добро пожаловать в умного бота VK\nДля работы с ботом Вам необходимо получить TOKEN на странице https://vkhost.github.io/\nПосле этого Вам будут предлагаться пользователи, с которыми вы можете познакомиться", vk
            )
        else:
            main_sender(event.user_id, f"Не понял твоей команды", vk)
