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
        credentials_path='credentials.json'
    ):
        self.api_base_url = api_base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.credentials_path = credentials_path
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

    moltin_api = MoltinAPI(api_base_url, client_id, client_secret)

    products = moltin_api.fetch_products()
    moltin_api.add_product_to_cart('new_cart', products[0]['id'], 2)
    cart = moltin_api.get_cart('new_cart')
    print(cart)

    cart_items = moltin_api.get_cart_items('new_cart')
    print(cart_items)