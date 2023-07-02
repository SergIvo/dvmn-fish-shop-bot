import logging

import telegram


class TgLogsHandler(logging.Handler):
    def __init__(self, tg_api_token, tg_chat_id):
        super().__init__()
        self.bot = telegram.Bot(token=tg_api_token)
        self.chat_id = tg_chat_id

    def emit(self, record):
        log_entry = self.format(record)
        self.bot.send_message(
            chat_id=self.chat_id,
            text=log_entry
        )
