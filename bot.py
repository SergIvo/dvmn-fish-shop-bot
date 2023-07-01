import logging
import redis

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Filters, Updater, CallbackQueryHandler, CommandHandler,
                          MessageHandler, CallbackContext)
from environs import Env
from moltin_api_methods import MoltinAPI

_database = None


def create_product_menu(moltin_api):
    products = moltin_api.fetch_products()
    keyboard = []
    for product in products:
        name = product['attributes']['name']
        keyboard.append(
            [InlineKeyboardButton(name, callback_data=product['id'])]
        )
    return InlineKeyboardMarkup(keyboard)


def start(update: Update, context: CallbackContext):
    moltin_api = context.bot_data.get('moltin_api')
    reply_markup = create_product_menu(moltin_api)

    if update.message:
        update.message.reply_text(text='Привет!', reply_markup=reply_markup)
    return 'HANDLE_DESCRIPTION'


def handle_menu(update: Update, context: CallbackContext):
    moltin_api = context.bot_data.get('moltin_api')
    reply_markup = create_product_menu(moltin_api)

    chat_id = update.callback_query.message.chat_id
    previous_message_id = update.callback_query.message.message_id
    context.bot.delete_message(
        chat_id,
        previous_message_id
    )
    context.bot.send_message(
        text='Выберите товар',
        chat_id=chat_id,
        reply_markup=reply_markup
    )
    return 'HANDLE_DESCRIPTION'


def handle_description(update: Update, context: CallbackContext):
    moltin_api = context.bot_data.get('moltin_api')
    product_id = update.callback_query.data
    product = moltin_api.fetch_product_by_id(product_id)
    product_image_id = product['relationships']['main_image']['data']['id']
    product_image = moltin_api.get_product_photo(product_image_id)
    image_url = product_image['link']['href']
    price = moltin_api.get_product_price(product['attributes']['sku'])

    message_text = f'''
        {product["attributes"]["name"]}
        {product["attributes"]["description"]}
        Price: ${price["attributes"]["currencies"]["USD"]["amount"] / 100}
    '''

    keyboard = [[InlineKeyboardButton('Назад', callback_data='menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    menu_message_id = update.callback_query.message.message_id
    chat_id = update.callback_query.message.chat_id
    context.bot.delete_message(
        chat_id,
        menu_message_id
    )
    context.bot.send_photo(
        caption=message_text,
        chat_id=chat_id,
        photo=image_url,
        reply_markup=reply_markup
    )
    return 'HANDLE_MENU'


def handle_users_reply(update: Update, context: CallbackContext):
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
        'HANDLE_DESCRIPTION': handle_description,
        'HANDLE_MENU': handle_menu
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
