import logging

from redis import Redis
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Filters, Updater, CallbackQueryHandler, CommandHandler,
                          MessageHandler, CallbackContext)
from environs import Env
from moltin_api_methods import MoltinAPI
from telegram_logging import TgLogsHandler

logger = logging.getLogger('fish-shop-bot')


def create_product_menu(moltin_api):
    products = moltin_api.fetch_products()
    keyboard = []
    for product in products:
        name = product['attributes']['name']
        keyboard.append(
            [InlineKeyboardButton(name, callback_data=product['id'])]
        )
    keyboard.append([InlineKeyboardButton('Корзина', callback_data='cart')])
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
    previous_message_id = update.callback_query.message.message_id
    chat_id = update.callback_query.message.chat_id

    if update.callback_query.data == 'cart':
        return handle_cart(update, context)
    elif update.callback_query.data == 'menu':
        return handle_menu(update, context)

    if '##' in update.callback_query.data:
        quantity, product_id = update.callback_query.data.split('##')
        cart_id = update.callback_query.message.chat_id
        moltin_api.add_product_to_cart(cart_id, product_id, int(quantity))

        previous_message_text = update.callback_query.message.caption
        previous_message_markup = update.callback_query.message.reply_markup
        context.bot.edit_message_caption(
            chat_id=chat_id,
            message_id=previous_message_id,
            caption=previous_message_text + '\nТовар добавлен в корзину.',
            reply_markup=previous_message_markup
        )
        return 'HANDLE_DESCRIPTION'

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

    keyboard = [
        [
            InlineKeyboardButton('1 кг', callback_data=f'1##{product_id}'),
            InlineKeyboardButton('5 кг', callback_data=f'5##{product_id}'),
            InlineKeyboardButton('10 кг', callback_data=f'10##{product_id}'),
        ],
        [
            InlineKeyboardButton('Назад', callback_data='menu'),
            InlineKeyboardButton('Корзина', callback_data='cart')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.delete_message(
        chat_id,
        previous_message_id
    )
    context.bot.send_photo(
        caption=message_text,
        chat_id=chat_id,
        photo=image_url,
        reply_markup=reply_markup
    )
    return 'HANDLE_DESCRIPTION'


def handle_cart(update: Update, context: CallbackContext):
    moltin_api = context.bot_data.get('moltin_api')
    previous_message_id = update.callback_query.message.message_id
    chat_id = update.callback_query.message.chat_id

    if update.callback_query.data == 'menu':
        return handle_menu(update, context)
    elif update.callback_query.data == 'pay':
        return request_email(update, context)
    elif not update.callback_query.data == 'cart':
        item_id = update.callback_query.data
        moltin_api.remove_cart_item(chat_id, item_id)

    cart_items = moltin_api.get_cart_items(chat_id)
    cart_description = ''
    keyboard = []
    for item in cart_items:
        product_price = item['meta']['display_price']['with_tax']['unit']['formatted']
        total_price = item['meta']['display_price']['with_tax']['value']['formatted']
        item_details = f'''
            {item['name']}
            {item['description']}
            {product_price} за кг
            {item['quantity']}кг в корзине общей стоимостью {total_price}\n
        '''
        cart_description += item_details

        keyboard.append(
            [InlineKeyboardButton(f'Убрать {item["name"]} из корзины', callback_data=f'{item["id"]}')]
        )
    cart = moltin_api.get_cart(chat_id)
    cart_price = cart['meta']['display_price']['with_tax']['formatted']
    cart_description += f'Итого: {cart_price}'

    keyboard.append(
        [
            InlineKeyboardButton('В меню', callback_data='menu'),
            InlineKeyboardButton('Оплатить', callback_data='pay')
        ]
    )
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.delete_message(
        chat_id,
        previous_message_id
    )
    context.bot.send_message(
        text=cart_description,
        chat_id=chat_id,
        reply_markup=reply_markup
    )
    return 'HANDLE_CART'


def request_email(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton('В меню', callback_data='menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        user_email = update.message.text
        user_name = update.effective_user.first_name
        moltin_api = context.bot_data.get('moltin_api')
        moltin_api.create_customer(user_name, user_email)

        confirmation = f'Запрос на оплату придет на почту {update.message.text}.'
        update.message.reply_text(text=confirmation, reply_markup=reply_markup)
        return 'HANDLE_MENU'
    elif update.callback_query.data == 'menu':
        return handle_menu(update, context)

    chat_id = update.callback_query.message.chat_id
    context.bot.send_message(
        text='Пожалуйста, напишите ваш адрес электронной почты.',
        chat_id=chat_id,
        reply_markup=reply_markup
    )
    return 'WAITING_EMAIL'


def handle_users_reply(update: Update, context: CallbackContext):
    if not context.bot_data.get('db'):
        context.bot_data['db'] = Redis.from_url(context.bot_data.get('db_url'))
    db = context.bot_data.get('db')

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
        'HANDLE_MENU': handle_menu,
        'HANDLE_CART': handle_cart,
        'WAITING_EMAIL': request_email
    }
    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(update, context)
        db.set(chat_id, next_state)
    except Exception as err:
        logger.exception(err)


if __name__ == '__main__':
    env = Env()
    env.read_env()
    tg_api_key = env('TG_API_KEY')
    moltin_api_url = env('EP_API_URL')
    moltin_client_id = env('EP_CLIENT_ID')
    moltin_client_secret = env('EP_CLIENT_SECRET')
    price_book_id = env('MOLTIN_PRICE_BOOK_ID')
    tg_log_chat_id = env('TG_LOG_CHAT_ID')

    logger.setLevel(logging.INFO)
    log_handler = TgLogsHandler(tg_api_key, tg_log_chat_id)
    log_handler.setFormatter(
        logging.Formatter('%(name)s %(levelname)s %(message)s')
    )
    logger.addHandler(log_handler)

    updater = Updater(tg_api_key)
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

    logger.info('Bot started')
    while True:
        try:
            updater.start_polling()
            updater.idle()
        except Exception as ex:
            logger.exception(ex)
