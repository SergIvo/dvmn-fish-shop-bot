import os
import logging
import redis

from telegram import Update
from telegram.ext import (Filters, Updater, CallbackQueryHandler, CommandHandler, 
    MessageHandler, CallbackContext, ConversationHandler)
from environs import Env

_database = None

def start(update: Update, context: CallbackContext):
    """
    Хэндлер для состояния START.
    
    Бот отвечает пользователю фразой "Привет!" и переводит его в состояние ECHO.
    Теперь в ответ на его команды будет запускаеться хэндлер echo.
    """
    update.message.reply_text(text='Привет!')
    return "ECHO"


def echo(update: Update, context: CallbackContext):
    """
    Хэндлер для состояния ECHO.
    
    Бот отвечает пользователю тем же, что пользователь ему написал.
    Оставляет пользователя в состоянии ECHO.
    """
    users_reply = update.message.text
    update.message.reply_text(users_reply)
    return "ECHO"


def handle_users_reply(update: Update, context: CallbackContext):
    """
    Функция, которая запускается при любом сообщении от пользователя и решает как его обработать.
    Эта функция запускается в ответ на эти действия пользователя:
        * Нажатие на inline-кнопку в боте
        * Отправка сообщения боту
        * Отправка команды боту
    Она получает стейт пользователя из базы данных и запускает соответствующую функцию-обработчик (хэндлер).
    Функция-обработчик возвращает следующее состояние, которое записывается в базу данных.
    Если пользователь только начал пользоваться ботом, Telegram форсит его написать "/start",
    поэтому по этой фразе выставляется стартовое состояние.
    Если пользователь захочет начать общение с ботом заново, он также может воспользоваться этой командой.
    """
    db = get_database_connection(update.chat_data.get('db_url'))
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = db.get(chat_id).decode("utf-8")
    
    states_functions = {
        'START': start,
        'ECHO': echo
    }
    state_handler = states_functions[user_state]
    # Если вы вдруг не заметите, что python-telegram-bot перехватывает ошибки.
    # Оставляю этот try...except, чтобы код не падал молча.
    # Этот фрагмент можно переписать.
    try:
        next_state = state_handler(bot, update)
        db.set(chat_id, next_state)
    except Exception as err:
        print(err)

def get_database_connection(database_url):
    """
    Возвращает конекшн с базой данных Redis, либо создаёт новый, если он ещё не создан.
    """
    global _database
    if _database is None:
        _database = redis.Redis.from_rl(database_url)
    return _database


if __name__ == '__main__':
    env = Env()
    env.read_env()
    token = env("TG_API_KEY")

    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.bot_data['db_url'] = env('REDIS_DB_URL')
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            'ECHO': [
                MessageHandler(Filters.text, echo)
            ]
        },
        fallbacks=[CommandHandler('quite', handle_users_reply)]
    )
    dispatcher.add_handler(conversation_handler)
    updater.start_polling()
