import threading
import schedule
import telebot
from apscheduler.schedulers.blocking import BlockingScheduler
from telebot import types
from check import *
import time
from apscheduler.schedulers.background import BackgroundScheduler

bot = telebot.TeleBot('#')
authorized_chat_ids = [#,#]  # List of user ID for all functionality to interact 

def is_user_authorized(chat_id):
    return chat_id in authorized_chat_ids

@bot.message_handler(commands=['start'])
def send_start_message(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    button = telebot.types.KeyboardButton('Ближайшее День рождение')
    button2 = telebot.types.KeyboardButton('Поиск по Фамилии')
    button3 = telebot.types.KeyboardButton('Добавить сотрудника')
    button4 = telebot.types.KeyboardButton('Удалить сотрудника')
    keyboard.add(button)
    keyboard.add(button2)
    keyboard.add(button3)
    keyboard.add(button4)
    bot.send_message(message.chat.id, 'Привет! Что бы вы хотели сделать?', reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text == 'Ближайшее День рождение')
def send_closest_birthday(message):
    db = DayBirth('DayBirth.db')
    db.find_nearest_birthday()
    db.print_nearest_employees()
    response = ""

    if db.nearest_employees:
        for employee in db.nearest_employees:
            name, formatted_birthday, birthday, diff = employee
            response += f"Сотрудник: {name}\n"
            response += f"Ближайший день рождения: {formatted_birthday}\n"
            response += f"Дата рождения: {birthday}\n"
            response += f"Осталось дней: {diff}\n\n"
    else:
        response = "Нет данных о сотрудниках с ближайшей датой рождения."

    bot.send_message(message.chat.id, response)

@bot.message_handler(func=lambda message: message.text == 'Поиск по Фамилии')
def search_employee_by_surname(message):
    bot.send_message(message.chat.id, "Введите фамилию сотрудника:")

    bot.register_next_step_handler(message, process_employee_surname)


def process_employee_surname(message):
    surname = message.text

    db = DayBirth('DayBirth.db')

    name_parts = surname.split()
    if len(name_parts) == 3:
        firstname = name_parts[1]
        patronymic = name_parts[2]
        formatted_date = db.search_person_birth(surname=surname,firstname=firstname, patronymic=patronymic)
        if formatted_date:
            formatted_date = formatted_date[0][1]
            bot.send_message(message.chat.id, f"Дата рождения сотрудника: {formatted_date}")
        else:
            bot.send_message(message.chat.id, "Сотрудник не найден.")
    else:
        formatted_dates = db.search_person_birth(surname)
        if formatted_dates:
            keyboard = create_employee_keyboard(formatted_dates)
            bot.send_message(message.chat.id, "Выберите сотрудника из списка:", reply_markup=keyboard)
        else:
            bot.send_message(message.chat.id, "Сотрудники с указанной фамилией не найдены.")


def create_employee_keyboard(employees):
    keyboard = types.InlineKeyboardMarkup()
    for employee in employees:
        name, formatted_date = employee
        button = types.InlineKeyboardButton(text=name, callback_data=formatted_date)
        keyboard.add(button)
    return keyboard


@bot.callback_query_handler(func=lambda call: True)
def process_employee_selection(call):
    formatted_date = call.data
    bot.send_message(call.message.chat.id, f"Дата рождения сотрудника: {formatted_date}")


@bot.message_handler(func=lambda message: message.text == 'Добавить сотрудника')
def add_employee(message):
    if is_user_authorized(message.chat.id):
        bot.send_message(message.chat.id, "Введите имя сотрудника:")

        bot.register_next_step_handler(message, process_employee_name_add)
    else:
        bot.send_message(message.chat.id, "У вас нет разрешения на добавление сотрудников.")

def process_employee_name_add(message):
    new_employee_name = message.text
    bot.send_message(message.chat.id, "Введите дату рождения сотрудника в формате ММ/ДД/ГГГГ:")

    bot.register_next_step_handler(message, process_birth_date_add, new_employee_name)

def process_birth_date_add(message, new_employee_name):
    new_birth_date = message.text
    if is_user_authorized(message.chat.id):
        db = DayBirth('DayBirth.db')  # Создаем экземпляр класса DayBirth
        formatted_date = db.add_employee_birth(new_employee_name, new_birth_date)
        if formatted_date:
            bot.send_message(message.chat.id, "Сотрудник успешно добавлен.")
        else:
            bot.send_message(message.chat.id, "Ошибка при добавлении сотрудника.")
    else:
        bot.send_message(message.chat.id, "У вас нет разрешения на добавление сотрудников.")

@bot.message_handler(func=lambda message: message.text == 'Удалить сотрудника')
def remove_employee(message):
    if is_user_authorized(message.chat.id):
        bot.send_message(message.chat.id, "Введите имя сотрудника для удаления:")

        bot.register_next_step_handler(message, process_employee_name_remove)
    else:
        bot.send_message(message.chat.id, "У вас нет разрешения на удаление сотрудников.")

def process_employee_name_remove(message):
    employee_name = message.text
    if is_user_authorized(message.chat.id):
        db = DayBirth('DayBirth.db')
        removed = db.remove_employee_birth(employee_name)
        if removed:
            bot.send_message(message.chat.id, f"Сотрудник {employee_name} успешно удален.")
        else:
            bot.send_message(message.chat.id, f"Не найдено сотрудника с именем {employee_name}.")
    else:
        bot.send_message(message.chat.id, "У вас нет разрешения на удаление сотрудников.")

def send_birthday_reminders():
    db = DayBirth('DayBirth.db')
    db.find_nearest_birthday()

    birthday_messages = []

    if db.nearest_employees:
        current_date = datetime.now().date()
        for employee in db.nearest_employees:
            name, formatted_birthday, birthday, diff = employee
            birth_date = datetime.strptime(birthday, "%m/%d/%Y").date()

            if diff <= 1:
                message = f"У {name} "
                if diff == 1:
                    message += f"через 1 день будет день рождения ({formatted_birthday})!"
                else:
                    message += f"сегодня день рождения ({formatted_birthday})!"
                birthday_messages.append(message)

    if birthday_messages:
        for user_id in authorized_chat_ids:
            bot.send_message(user_id, "\n".join(birthday_messages))

def run_bot():
    try:
        bot.polling(none_stop=True)

    except Exception as e:
        print(f"Ошибка при выполнении бота: {e}")
        time.sleep(5)

def run_scheduler():
    scheduler = BlockingScheduler()
    scheduler.add_job(send_birthday_reminders, 'cron', hour=4, minute=38)
    scheduler.start()

    try:
        while True:
            time.sleep(1)
            scheduler.print_jobs()

    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

bot_thread = threading.Thread(target=run_bot)
scheduler_thread = threading.Thread(target=run_scheduler)

bot_thread.start()
scheduler_thread.start()

bot_thread.join()
scheduler_thread.join()

