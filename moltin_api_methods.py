import json
import time
from os.path import exists
from urllib.parse import urljoin

import requests
from environs import Env


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
        self.api_token = self.get_access_token()

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

    def fetch_products(self):
        headers = {'Authorization': f'Bearer {self.api_token}'}
        url = urljoin(self.api_base_url, 'pcm/products')
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()['data']

    def fetch_product_by_id(self, product_id):
        headers = {'Authorization': f'Bearer {self.api_token}'}
        url = urljoin(self.api_base_url, f'pcm/products/{product_id}')
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()['data']

    def get_product_price(self, product_sku):
        headers = {'Authorization': f'Bearer {self.api_token}'}
        url = urljoin(self.api_base_url, f'pcm/pricebooks/{self.price_book}/prices')
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        filtered_price = [
            price for price in response.json()['data'] if price['attributes']['sku'] == product_sku
        ]
        return filtered_price[0]

    def get_product_photo(self, photo_id):
        headers = {'Authorization': f'Bearer {self.api_token}'}
        url = urljoin(self.api_base_url, f'v2/files/{photo_id}')
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()['data']

    def add_product_to_cart(self, cart_id, product_id, quantity):
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        url = urljoin(self.api_base_url, f'v2/carts/{cart_id}/items')
        payload = {
            'data': {
                'id': product_id,
                'type': 'cart_item',
                'quantity': quantity
            }
        }
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()['data']

    def get_cart(self, cart_id):
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        url = urljoin(self.api_base_url, f'v2/carts/{cart_id}')
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()['data']

    def remove_cart_item(self, cart_id, item_id):
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        url = urljoin(self.api_base_url, f'v2/carts/{cart_id}/items/{item_id}')
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        return response.json()['data']

    def create_customer(self, name, email):
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        url = urljoin(self.api_base_url, f'v2/customers')
        payload = {
            'data': {
                'type': 'customer',
                'name': name,
                'email': email
            }
        }
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()['data']

    def get_customer(self, customer_id):
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        url = urljoin(self.api_base_url, f'v2/customers/{customer_id}')
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()['data']

    def get_cart_items(self, cart_id):
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        url = urljoin(self.api_base_url, f'v2/carts/{cart_id}/items')
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()['data']


if __name__ == '__main__':
    env = Env()
    env.read_env()
    api_base_url = env('EP_API_URL')
    client_id = env('EP_CLIENT_ID')
    client_secret = env('EP_CLIENT_SECRET')
    price_book_id = env('MOLTIN_PRICE_BOOK_ID')

    moltin_api = MoltinAPI(api_base_url, client_id, client_secret, price_book_id)

    customer = moltin_api.create_customer('New Customer', 'mail@sample.com')
    print(customer)
    customer_info = moltin_api.get_customer(customer['id'])
    print(customer_info)
