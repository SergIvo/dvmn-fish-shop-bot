import logging
import redis

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Filters, Updater, CallbackQueryHandler, CommandHandler, 
                          MessageHandler, CallbackContext)
from environs import Env
from moltin_api_methods import MoltinAPI

_database = None


def start(update: Update, context: CallbackContext):
    moltin_api = context.bot_data.get('moltin_api')
    products = moltin_api.fetch_products()
    keyboard = []
    for product in products:
        keyboard.append(
            [InlineKeyboardButton(product['attributes']['name'], callback_data=product['id'])]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(text='Привет!', reply_markup=reply_markup)
    return 'HANDLE_MENU'


def echo(update: Update, context: CallbackContext):
    if update.message:
        user_reply = update.message.text
        update.message.reply_text(user_reply)
    else:
        user_reply = update.callback_query.data
        update.callback_query.message.reply_text(user_reply)
    return 'ECHO'


def handle_menu(update: Update, context: CallbackContext):
    moltin_api = context.bot_data.get('moltin_api')
    product_id = update.callback_query.data
    product = moltin_api.fetch_product_by_id(product_id)
    price = moltin_api.get_product_price(product['attributes']['sku'])
    
    message_text = f'''
        {product["attributes"]["name"]}
        {product["attributes"]["description"]}
        Price: ${price["attributes"]["currencies"]["USD"]["amount"] / 100}
    '''
    update.callback_query.message.reply_text(message_text)
    return 'START'


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
    db = get_database_connection(context.bot_data.get('db_url'))
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
        'HANDLE_MENU': handle_menu,
        'ECHO': echo
    }
    state_handler = states_functions[user_state]
    # Если вы вдруг не заметите, что python-telegram-bot перехватывает ошибки.
    # Оставляю этот try...except, чтобы код не падал молча.
    # Этот фрагмент можно переписать.
    try:
        next_state = state_handler(update, context)
        db.set(chat_id, next_state)
    except Exception as err:
        print(err)


def get_database_connection(database_url):
    global _database
    if _database is None:
        _database = redis.Redis.from_url(database_url)
    return _database


if __name__ == '__main__':
    env = Env()
    env.read_env()
    token = env('TG_API_KEY')
    moltin_api_url = env('EP_API_URL')
    moltin_client_id = env('EP_CLIENT_ID')
    moltin_client_secret = env('EP_CLIENT_SECRET')
    price_book_id = env('MOLTIN_PRICE_BOOK_ID')

    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.bot_data['db_url'] = env('REDIS_DB_URL')
    dispatcher.bot_data['moltin_api'] = MoltinAPI(
        moltin_api_url,
        moltin_client_id,
        moltin_client_secret,
        price_book_id
    )
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))
    updater.start_polling()
