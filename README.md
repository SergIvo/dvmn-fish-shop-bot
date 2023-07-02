# Fish Shop Bot

## About

This is a simple Telegram bot wich works as a fish shop, allowing user to choose a product, add it to cart, view products in the cart and remove them from the cart. Bot utilizes Elastic Path API to get information about products, create and store cart and customer personal data.

Bot is now available [here](http://t.me/dmn_fishbot)

This project created for educational purposes as part of an online course for web developers at [dvmn.org](https://dvmn.org/)

## Preparing project to run

1. Download files from GitHub with `git clone` command:
```
https://github.com/SergIvo/dvmn-fish-shop-bot
```
2. Create virtual environment using python [venv](https://docs.python.org/3/library/venv.html) to avoid conflicts with different versions of the same packages:
```
python -m venv venv
```
3. Then install dependencies from "requirements.txt" in created virtual environment using `pip` package manager:
```
pip install -r requirements.txt
```
4. To run the project scripts, you should first set some environment variables. To make environment variable management easier, you can create [.env](https://pypi.org/project/python-dotenv/#getting-started) file and store all variables in it. Following variable are required to run project:
```
EP_CLIENT_ID=<your Elastic Path Client ID>
EP_CLIENT_SECRET=<your Elastic Path Secret>
EP_API_URL=<your Elastic Path API URL>
```
To get these variables, you should open "Application Keys" page from left side menu in your Elastic Path personal account, in the "System" section, and press "Create New" button to create application key, if you didn't. After creating application key client ID, client secret and API base URL will be displayed on "Application Keys" page. API base URL depends on region you are in, you can read more about [it here](https://elasticpath.dev/docs/commerce-cloud/api-overview/elastic-path-domains).
```
MOLTIN_PRICE_BOOK_ID=<your price book ID>
```
To get price book ID, you should open "Price Books" page from left side menu in your Elastic Path personal account, in the "Product Expirience Manager" section. Click on your price book to open price book editor page. Price book ID will be displayed in the header of this page.
```
REDIS_DB_URL=redis://[[username]:[password]]@host:port/database
```
You can read through [this part](https://redis.readthedocs.io/en/latest/connections.html#redis.Redis) of Redis documentation to know more about types of database URLs Redis can connect to.
```
TG_API_KEY=<your Telegram bot API key>
TG_LOG_CHAT_ID=<log chat ID>
```
Log chat ID is the ID of the chat to wich bot should send logs.

## Running bot

To run Telegram bot, execute the following command:
```
python bot.py
```

