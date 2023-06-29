import json
import time
from os.path import exists
from urllib.parse import urljoin

import requests
from environs import Env


def fetch_ep_credentials(api_base_url, client_id, client_secret):
    url = urljoin(api_base_url, 'oauth/access_token')
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    response = requests.post(url, data=payload)
    response.raise_for_status()
    return response.json()


def get_access_token(credentials_path, api_base_url, client_id, client_secret):
    if exists(credentials_path):
        with open(credentials_path, 'r') as json_file:
            credentials = json.loads(json_file.read())

        current_time = time.time()
        expiration_time = credentials.get('expires')
        if current_time < expiration_time:
            return credentials.get('access_token')

    credentials = fetch_ep_credentials(api_base_url, client_id, client_secret)
    with open(credentials_path, 'w') as json_file:
        json_file.write(json.dumps(credentials))
    return credentials.get('access_token')


def fetch_products(api_base_url, api_token):
    headers = {'Authorization': f'Bearer {api_token}'}
    url = url = urljoin(api_base_url, 'pcm/products')
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']


def add_product_to_cart(api_base_url, api_token, cart_id, product_id, quantity):
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    url = urljoin(api_base_url, f'v2/carts/{cart_id}/items')
    payload = {
        'data': {
            'id': product_id, 
            'type': 'cart_item', 
            'quantity': quantity
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    try:
        response.raise_for_status()
    except:
        print(response.text)
    return response.json()['data']


def get_cart(api_base_url, api_token, cart_id):
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    url = url = urljoin(api_base_url, f'v2/carts/{cart_id}')
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']


def get_cart_items(api_base_url, api_token, cart_id):
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    url = url = urljoin(api_base_url, f'v2/carts/{cart_id}/items')
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']


if __name__ == '__main__':
    env = Env()
    env.read_env()
    api_base_url = env('EP_API_URL')
    client_id = env('EP_CLIENT_ID')
    client_secret = env('EP_CLIENT_SECRET')



    moltin_access_token = get_access_token('credentials.json', api_base_url, client_id, client_secret)
    print(moltin_access_token)
    products = fetch_products(api_base_url, moltin_access_token)
    add_product_to_cart(api_base_url, moltin_access_token, 'new_cart', products[0]['id'], 2)
    cart = get_cart(api_base_url, moltin_access_token, 'new_cart')
    print(cart)
    
    cart_items = get_cart_items(api_base_url, moltin_access_token, 'new_cart')
    print(cart_items)
