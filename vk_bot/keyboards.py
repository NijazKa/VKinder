from vk_api.keyboard import VkKeyboard, VkKeyboardColor

# Создание клавиатуры
keyboard = VkKeyboard(one_time=True)
keyboard.add_button('Лайк', color=VkKeyboardColor.POSITIVE) 
keyboard.add_button('Вперед', color=VkKeyboardColor.SECONDARY)
keyboard.add_button('Избранное', color=VkKeyboardColor.PRIMARY)
keyboard.add_button('Справка', color=VkKeyboardColor.PRIMARY)