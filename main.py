import json
import time
from os.path import exists
from urllib.parse import urljoin

import requests
from environs import Env


def fetch_ep_credentials(api_base_url, client_id, client_secret):
    url = urljoin(api_base_url, 'oauth/access_token')
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    response = requests.post(url, data=data)
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


if __name__ == '__main__':
    env = Env()
    env.read_env()
    api_base_url = env('EP_API_URL')
    client_id = env('EP_CLIENT_ID')
    client_secret = env('EP_CLIENT_SECRET')



    moltin_access_token = get_access_token('credentials.json', api_base_url, client_id, client_secret)
    print(moltin_access_token)

    
