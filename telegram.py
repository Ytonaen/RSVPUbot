import os  # Импортируем os для работы с переменными окружения
import telebot
from telebot import types
import json
import random

# Получаем токен из переменной окружения
bot_token = os.environ.get("TOKEN")

# Проверяем, установлен ли токен
if not bot_token:
    raise ValueError("Токен бота не установлен в переменной окружения 'TOKEN'")

# Define the data file path
data_file = "user_data.json"

#Подгружаем фаил пользователя
try:
    with open(data_file, "r") as f:
        user_data = json.load(f)
except FileNotFoundError:
    user_data = {}

def save_user_data():
    global user_data
    with open(data_file, "w") as f:
        json.dump(user_data, f)

def get_user_counter(chat_id):
    if str(chat_id) not in user_data:
        user_data[str(chat_id)] = {
            "counter": 0,
            "counters": {"Q": 0, "W": 0, "E": 0, "R": 0, "T": 0},
            "used_images": [],
            "group_usage": {group: 0 for group in image_groups.keys()}  #Группы входят в студию
        }
    return user_data[str(chat_id)]

def update_user_counter(chat_id, key, value):
    user_data[str(chat_id)][key] = value
    save_user_data()

def send_text_file(message, file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
        bot.send_message(message.chat.id, text)

# Определяем группы картинок
image_groups = {
    'group1': ['image.jpg', 'image1.jpg', 'image2.jpg', 'image3.jpg'],
    'group2': ['image4.jpg', 'image5.jpg', 'image6.jpg', 'image7.jpg'],
    'group3': ['image8.jpg', 'image9.jpg', 'image10.jpg', 'image11.jpg'],
    'group4': ['image12.jpg', 'image13.jpg', 'image14.jpg', 'image15.jpg'],
    'group5': ['image16.jpg', 'image17.jpg', 'image18.jpg', 'image20.jpg']
}

# Определяем кнопки для каждой группы
group_buttons = {
    'group1': 'Q',
    'group2': 'W',
    'group3': 'E',
    'group4': 'R',
    'group5': 'T'
}

def send_image_pair(message):
    chat_id = message.chat.id
    user_counters = get_user_counter(chat_id)
    used_images = user_counters["used_images"]
    group_usage = user_counters["group_usage"]

    # Выбераем группы, которые еще не достигли лимита использования (4 раза)
    available_groups = [group for group, usage in group_usage.items() if usage < 4]

    # Если доступно только две группы, выбираем их
    if len(available_groups) >= 2:
        groups = random.sample(available_groups, 2)
    elif len(available_groups) == 1:
        groups = available_groups
    else:
        # Если доступных групп нет, то выводим сообщение и выходим из функции
        bot.send_message(chat_id, "Нет доступных групп для отправки изображений.")
        return

    # Если доступны только две группы, используем их
    if len(groups) < 2:
        # Если осталась только одна группа, используем ее
        groups = available_groups

    # Выбераем случайную картинку из каждой группы, исключая использованные изображения
    image1 = None
    image2 = None

    for group in groups:
        # Выбираем случайную картинку из группы, которая еще не использовалась
        while True:
            random_image = random.choice(image_groups[group])
            if random_image not in used_images:
                if image1 is None:
                    image1 = (group, random_image)
                elif image2 is None and group != image1[0]:
                    image2 = (group, random_image)
                break

    # Если не удалось выбрать две разные картинки, дублируем первую
    if image2 is None:
        image2 = image1

    # Добавляем использованные изображения в список
    used_images.extend([image1[1], image2[1]])
    user_counters["used_images"] = used_images
    update_user_counter(chat_id, "used_images", used_images)

    # Обновляем использование групп
    group_usage[image1[0]] += 1
    group_usage[image2[0]] += 1
    user_counters["group_usage"] = group_usage
    update_user_counter(chat_id, "group_usage", group_usage)

    # Костыль для красивой отправки по бкоам друг от друга
    media = [
        types.InputMediaPhoto(open(image1[1], 'rb')),
        types.InputMediaPhoto(open(image2[1], 'rb'))
    ]
    bot.send_media_group(message.chat.id, media)

    # Создаем кнопки для каждой группы
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    item1 = types.KeyboardButton(group_buttons[image1[0]])
    item2 = types.KeyboardButton(group_buttons[image2[0]])
    markup.add(item1, item2)

    bot.send_message(message.chat.id, "Выберите картинку которая вам больше нравится:", reply_markup=markup)

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user_counters = get_user_counter(chat_id)

    # Сброс всех счетчиков
    user_counters["counter"] = 0  # Сброс счетчика для новой игры
    user_counters["counters"] = {"Q": 0, "W": 0, "E": 0, "R": 0, "T": 0}  # Сброс счетчиков для новой игры
    user_counters["used_images"] = []  # Сброс использованных изображений
    user_counters["group_usage"] = {group: 0 for group in image_groups.keys()}  # Сброс использования групп

    # Сохранение обновленных данных
    update_user_counter(chat_id, "counter", 0)
    update_user_counter(chat_id, "counters", user_counters["counters"])
    update_user_counter(chat_id, "group_usage", user_counters["group_usage"])
    update_user_counter(chat_id, "used_images", [])

    bot.send_message(chat_id, "Начнем игру..")
    send_image_pair(message)

def send_end_message(message, counters):
    chat_id = message.chat.id
    user_counters = get_user_counter(chat_id)
    counter = user_counters["counter"]  # Смотрим текущий счетчик пользователя

    if counter >= 10:  # Чекаем послкедний ли вопрос
        max_counter = max(counters.values())
        max_counters = [key for key, value in counters.items() if value == max_counter]

        if len(max_counters) > 1:
            # Если есть несколько максимальных значений, отправляем на дополнительный вопрос
            send_image_pair(message)
        else:
            key = max_counters[0]
            if key == 'Q':
                end_message = "Ситуация 1: ..."
                info_message = "Дополнительная информация #1"
            elif key == 'W':
                end_message = "Ситуация 2: ..."
                info_message = "Дополнительная информация #2"
            elif key == 'E':
                end_message = "Ситуация 3: ..."
                info_message = "Дополнительная информация #3"
            elif key == 'R':
                end_message = "Ситуация 4: ..."
                info_message = "Дополнительная информация #4"
            elif key == 'T':
                end_message = "Ситуация 5: ..."
                info_message = "Дополнительная информация #5"

            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            item1 = types.KeyboardButton('Рестарт')
            item2 = types.KeyboardButton(info_message)
            markup.add(item1, item2)

            bot.send_message(chat_id, end_message, reply_markup=markup)
            bot.send_message(chat_id, "Ваши счетчики: Q - {}, W - {}, E - {}, R - {}, T - {}".format(counters["Q"], counters["W"], counters["E"], counters["R"], counters["T"]))

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    user_counters = get_user_counter(chat_id)
    counter = user_counters["counter"]
    counters = user_counters["counters"]

    # Определяем действия в виде словаря
    actions = {
        'Q': 2,
        'W': 2,
        'E': 2,
        'R': 2,
        'T': 2,
        'Рестарт': 0
    }

    # Проверяем, есть ли действие в словаре
    if message.text in actions:
        delta_counter = actions[message.text]
        if message.text != 'Рестарт':
            counters[message.text] += delta_counter
            update_user_counter(chat_id, "counters", counters)
        else:
            # Сброс счетчиков при нажатии "Рестарт"
            counters = {"Q": 0, "W": 0, "E": 0, "R": 0, "T": 0}
            update_user_counter(chat_id, "counters", counters)

            # Сброс общего счетчика
            counter = 0
            update_user_counter(chat_id, "counter", counter)

            # Сброс использованных изображений
            user_counters["used_images"] = []
            update_user_counter(chat_id, "used_images", [])

            # Сброс использования групп
            user_counters["group_usage"] = {group: 0 for group in image_groups.keys()}  # Reset group usage
            update_user_counter(chat_id, "group_usage", user_counters["group_usage"])

            bot.send_message(chat_id, "Чтож начнем заново...")

        # Обновляем счетчики
        counter += 1
        update_user_counter(chat_id, "counter", counter)

    # Обработка дополнительных сообщений
    elif message.text.startswith('Дополнительная информация'):
        info_number = message.text.split('#')[1].strip()
        file_path = f"texts/text{info_number}.txt"
        send_text_file(message, file_path)  # Отправляем файл
        # Обновляем счетчики (если необходимо)
        update_user_counter(chat_id, "counter", counter)
        update_user_counter(chat_id, "counters", counters)

    else:
        bot.send_message(chat_id, "Выберите одну из картинок")

    if counter >= 10:  # Check if it's the last question
        send_end_message(message, counters)
        return

    send_image_pair(message)

bot.polling()
