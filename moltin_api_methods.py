import json
import time
from os.path import exists
from urllib.parse import urljoin

import requests


class MoltinAPI():
    def __init__(
        self,
        api_base_url,
        client_id,
        client_secret,
        price_book_id,
        credentials_path='credentials.json'
    ):
        self.api_base_url = api_base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.credentials_path = credentials_path
        self.price_book = price_book_id
        self.headers = {
            'Authorization': f'Bearer {self.get_access_token()}'
        }

    def fetch_ep_credentials(self):
        url = urljoin(self.api_base_url, 'oauth/access_token')
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials'
        }
        response = requests.post(url, data=payload)
        response.raise_for_status()
        return response.json()

    def get_access_token(self):
        if exists(self.credentials_path):
            with open(self.credentials_path, 'r') as json_file:
                credentials = json.loads(json_file.read())

            current_time = time.time()
            expiration_time = credentials.get('expires')
            if current_time < expiration_time:
                return credentials.get('access_token')

        credentials = self.fetch_ep_credentials()
        with open(self.credentials_path, 'w') as json_file:
            json_file.write(json.dumps(credentials))
        return credentials.get('access_token')

    def make_get_request(self, url):
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()['data']

    def fetch_products(self):
        url = urljoin(self.api_base_url, 'pcm/products')
        return self.make_get_request(url)

    def fetch_product_by_id(self, product_id):
        url = urljoin(self.api_base_url, f'pcm/products/{product_id}')
        return self.make_get_request(url)

    def get_product_price(self, product_sku):
        url = urljoin(self.api_base_url, f'pcm/pricebooks/{self.price_book}/prices')
        prices = self.make_get_request(url)
        filtered_price = [
            price for price in prices if price['attributes']['sku'] == product_sku
        ]
        return filtered_price[0]

    def get_product_photo(self, photo_id):
        url = urljoin(self.api_base_url, f'v2/files/{photo_id}')
        return self.make_get_request(url)

    def add_product_to_cart(self, cart_id, product_id, quantity):
        url = urljoin(self.api_base_url, f'v2/carts/{cart_id}/items')
        payload = {
            'data': {
                'id': product_id,
                'type': 'cart_item',
                'quantity': quantity
            }
        }
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()['data']

    def get_cart(self, cart_id):
        url = urljoin(self.api_base_url, f'v2/carts/{cart_id}')
        return self.make_get_request(url)

    def get_cart_items(self, cart_id):
        url = urljoin(self.api_base_url, f'v2/carts/{cart_id}/items')
        return self.make_get_request(url)

    def remove_cart_item(self, cart_id, item_id):
        url = urljoin(self.api_base_url, f'v2/carts/{cart_id}/items/{item_id}')
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()
        return response.json()['data']

    def create_customer(self, name, email):
        url = urljoin(self.api_base_url, 'v2/customers')
        payload = {
            'data': {
                'type': 'customer',
                'name': name,
                'email': email
            }
        }
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()['data']

    def get_customer(self, customer_id):
        url = urljoin(self.api_base_url, f'v2/customers/{customer_id}')
        return self.make_get_request(url)
