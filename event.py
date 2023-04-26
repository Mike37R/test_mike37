import telebot
from telebot import types
import sqlite3
from datetime import datetime, timedelta

TOKEN = 'ID'
bot = telebot.TeleBot(TOKEN)
user_data = {}
GROUP_ID = GROUP_ID

def create_db():
    conn = sqlite3.connect('events.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE events (id INTEGER PRIMARY KEY AUTOINCREMENT, date text, end_date text, event text, user text, notification boolean)''')
    conn.commit()
    conn.close()

def add_event(date, end_date, event, user):
    conn = sqlite3.connect('events.db')
    c = conn.cursor()
    c.execute("INSERT INTO events (date, end_date, event, user, notification) VALUES (?,?,?,?,?)", (date, end_date, event, user, False))
    conn.commit()
    conn.close()

def check_events():
    today = datetime.now().strftime('%d.%m.%Y')
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%d.%m.%Y')
    conn = sqlite3.connect('events.db')
    c = conn.cursor()
    c.execute("SELECT * FROM events WHERE date=? AND notification=?", (today,False))
    today_events = c.fetchall()
    c.execute("SELECT * FROM events WHERE date=? AND notification=?", (tomorrow,False))
    tomorrow_events = c.fetchall()
    conn.close()
    return today_events, tomorrow_events

def get_upcoming_events():
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect('events.db')
    c = conn.cursor()
    c.execute("SELECT * FROM events WHERE date>=?", (today,))
    upcoming_events = c.fetchall()
    conn.close()
    return upcoming_events

def update_notification(event_id):
    conn = sqlite3.connect('events.db')
    c = conn.cursor()
    c.execute("UPDATE events SET notification=? WHERE id=?", (True,event_id))
    conn.commit()
    conn.close()

def delete_event(event_id):
    conn = sqlite3.connect('events.db')
    c = conn.cursor()
    c.execute("DELETE FROM events WHERE id=?", (event_id,))
    conn.commit()
    conn.close()

def update_event_date(event_id, new_date):
    conn = sqlite3.connect('events.db')
    c = conn.cursor()
    c.execute("UPDATE events SET date=? WHERE id=?", (new_date,event_id))
    conn.commit()
    conn.close()

try:
    create_db()

except:
    pass

@bot.message_handler(commands=['+'])
def add_command(message):
    msg = bot.send_message(GROUP_ID, "Укажите дату начала события (ДД.ММ.ГГГГ) 📅")
    bot.register_next_step_handler(msg, process_date_step)
def process_date_step(message):
    try:
        date = message.text
        user_data[message.chat.id] = {'date': date}
        msg = bot.send_message(GROUP_ID, "Укажите дату окончания события (ДД.ММ.ГГГГ) 📅")
        bot.register_next_step_handler(msg, process_end_date_step)
    except Exception as e:
        bot.reply_to(message, 'Ошибка 😞')

def process_end_date_step(message):
    try:
        end_date = message.text
        user_data[message.chat.id]['end_date'] = end_date
        msg = bot.send_message(GROUP_ID, "Укажите название события 📝")
        bot.register_next_step_handler(msg, process_event_step)
    except Exception as e:
        bot.reply_to(message, 'Ошибка 😞')

def process_event_step(message):
    try:
        event = message.text
        date = user_data[message.chat.id]['date']
        end_date = user_data[message.chat.id]['end_date']
        add_event(date, end_date, event, message.from_user.username)
        bot.send_message(GROUP_ID, "Событие успешно добавлено ✅")
        user_data.pop(message.chat.id)
        
    except Exception as e:
        bot.reply_to(message, 'Ошибка 😞')

@bot.message_handler(commands=['события'])
def events_command(message):
    upcoming_events = get_upcoming_events()
    
for event in upcoming_events:
		markup = types.InlineKeyboardMarkup(row_width=2)
		cancel_button = types.InlineKeyboardButton("Отменить", callback_data=f"cancel_{event[0]}")
		reschedule_button = types.InlineKeyboardButton("Перенести", callback_data=f"reschedule_{event[0]}")
		markup.add(cancel_button,reschedule_button)
		bot.send_message(GROUP_ID, f"{event[1]} {event[3]}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('cancel'))
def cancel_callback(call):
    event_id = int(call.data.split("_")[1])
    delete_event(event_id)
    bot.answer_callback_query(call.id, "Событие отменено")
    bot.edit_message_text("Событие отменено", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('reschedule'))
def reschedule_callback(call):
    event_id = int(call.data.split("_")[1])
    user_data[call.from_user.id] = {'event_id': event_id}
    msg = bot.send_message(call.message.chat.id, "Укажите новую дату события (ДД.ММ.ГГГГ)")
    bot.register_next_step_handler(msg, process_reschedule_step)

def process_reschedule_step(message):
    try:
        new_date = message.text
        event_id = user_data[message.from_user.id]['event_id']
        update_event_date(event_id, new_date)
        bot.send_message(GROUP_ID, "Дата события успешно изменена")
        user_data.pop(message.from_user.id)
        
    except Exception as e:
        bot.reply_to(message, 'Ошибка 😞')
while True:
    today_events, tomorrow_events = check_events()
    
for event in today_events:
        bot.send_message(GROUP_ID, f"{event[1]}, {event[3]} ({event[4]})")
        update_notification(event[0])
        
for event in tomorrow_events:
        bot.send_message(GROUP_ID, f"{event[1]}, {event[3]} ({event[4]})")
        update_notification(event[0])
        
time.sleep(86400)

bot.polling()
