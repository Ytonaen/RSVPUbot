import os  # Импортируем os для работы с переменными окружения
import telebot
from telebot import types
import json  # To store and retrieve data from a file

# Получаем токен из переменной окружения
bot_token = os.environ.get("TOKEN")

# Проверяем, установлен ли токен
if not bot_token:
    raise ValueError("Токен бота не установлен в переменной окружения 'TOKEN'")

# Создаем экземпляр бота с токеном
bot = telebot.TeleBot(bot_token)
# Define the data file path
data_file = "user_data.json"

# Load user data from the file (empty dict if no file exists)
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
        user_data[str(chat_id)] = {"counter": 0, "counterpoints": 0}
    return user_data[str(chat_id)]


def update_user_counter(chat_id, key, value):
    user_data[str(chat_id)][key] = value
    save_user_data()


# Define the image paths
image_pairs = [
    ('image1.jpg', 'image2.jpg'),
    ('image3.jpg', 'image4.jpg'),
    ('image5.jpg', 'image6.jpg'),
    ('image7.jpg', 'image8.jpg'),
    ('image9.jpg', 'image10.jpg'),
    ('image11.jpg', 'image12.jpg'),
]

def send_text_file(message, file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
        bot.send_message(message.chat.id, text)

def send_image_pair(message, pair_index):
    global user_data
    chat_id = message.chat.id
    user_counters = get_user_counter(chat_id)
    counter = user_counters["counter"]
    counterpoints = user_counters["counterpoints"]
    image1, image2 = image_pairs[pair_index]

    # Create a media group to send images side-by-side
    media = [
        types.InputMediaPhoto(open(image1, 'rb')),
        types.InputMediaPhoto(open(image2, 'rb'))
    ]
    bot.send_media_group(chat_id, media)

    if counter >= 2:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        item1 = types.KeyboardButton('Q')
        item2 = types.KeyboardButton('W')
        markup.add(item1, item2)
    else:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        item1 = types.KeyboardButton('Левая лучше')
        item2 = types.KeyboardButton('Правая лучше')
        markup.add(item1, item2)


    bot.send_message(chat_id, "Выберите картинку которая вам больше нравится:", reply_markup=markup)
    


@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user_counters = get_user_counter(chat_id)
    user_counters["counter"] = 0  # Reset counter for new game
    update_user_counter(chat_id, "counter", 0)
    user_counters["counterpoints"] = 0  # Reset counter for new game
    update_user_counter(chat_id, "counterpoints", 0)

    bot.send_message(chat_id, "Начнем игру..")
    send_image_pair(message, 0)

def send_end_message(message, counterpoints):
    chat_id = message.chat.id
    user_counters = get_user_counter(chat_id)
    counter = user_counters["counter"]  # Access counter from user data

    if counter == 6:  # Check if it's the last question
        if counterpoints <= -5:
            end_message = "Ситуация 1: ..."
            info_message = "Дополнительная информация #1"
        elif -5 < counterpoints <= 0:
            end_message = "Ситуация #2: ..."
            info_message = "Дополнительная информация #2"
        elif 0 < counterpoints <= 5:
            end_message = "Ситуация #3: ..."
            info_message = "Дополнительная информация #3"
        else:
            end_message = "Ситуация #4: ..."
            info_message = "Дополнительная информация #4"


        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        item1 = types.KeyboardButton('Рестарт')
        item2 = types.KeyboardButton(info_message)
        markup.add(item1, item2)

        bot.send_message(chat_id, end_message, reply_markup=markup)
        bot.send_message(chat_id, f"Ваш счет: {counterpoints}")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    user_counters = get_user_counter(chat_id)
    counter = user_counters["counter"]
    counterpoints = user_counters["counterpoints"]

    # Определяем действия в виде словаря
    actions = {
        'Левая лучше': (1, -1),
        'Правая лучше': (1, 1),
        'Q': (1, -2),
        'W': (1, 2),
        'Рестарт': (0, 0)
    }

    # Проверяем, есть ли действие в словаре
    if message.text in actions:
        delta_counter, delta_counterpoints = actions[message.text]
        counter += delta_counter
        counterpoints += delta_counterpoints
        
        if message.text == 'Рестарт':
            counterpoints = 0
            counter = 0
            update_user_counter(chat_id, "counter", counter)
            update_user_counter(chat_id, "counterpoints", counterpoints)
            bot.send_message(chat_id, "Чтож начнем заново...")
            
        
        # Обновляем счетчики
        update_user_counter(chat_id, "counter", counter)
        update_user_counter(chat_id, "counterpoints", counterpoints)

    # Обработка дополнительных сообщений
    elif message.text.startswith('Дополнительная информация'):
        info_number = message.text.split('#')[1].strip()
        file_path = f"texts/text{info_number}.txt"
        send_text_file(message, file_path)  # Отправляем файл
        # Обновляем счетчики (если необходимо)
        update_user_counter(chat_id, "counter", counter)
        update_user_counter(chat_id, "counterpoints", counterpoints)

    else:
        bot.send_message(chat_id, "Выберите одну из картинок")

    if counter == 6:  # Check if it's the last question
        send_end_message(message, counterpoints)
        return

    next_pair_index = counter
    bot.send_message(chat_id, f"для дебагинга: {counter}")
    send_image_pair(message, next_pair_index)





bot.polling()
