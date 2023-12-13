import datetime
import environ
import hashlib
import hmac
import json
import os
import requests
from django.conf import settings
from base64 import b64decode, b64encode
from pathlib import Path
from O365 import Account
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP

from .token import DjangoCacheTokenBackend



BASE_DIR = Path(__file__).resolve().parent.parent.parent
GRAPH_URL = 'https://graph.microsoft.com/v1.0'
EXPIRATION_DURATION = datetime.timedelta(minutes=4230)
PEM_DATA = open(os.path.join(BASE_DIR, 'cert.pem'), 'rb').read()
PRIVATE_KEY = RSA.import_key(open(os.path.join(BASE_DIR, 'key.pem'), 'rb').read())

env = environ.Env()

def get_or_set_account():
    credentials = (env('O365_CLIENT'), env('O365_SECRET'))
    token_backend = DjangoCacheTokenBackend()
    account = Account(credentials, 
                      auth_flow_type='credentials', 
                      tenant_id=env('O365_TENANT'),
                      token_backend=token_backend,
                      )
    if account.is_authenticated or account.authenticate():
        return account
    
    raise RuntimeError('Could not authenticate. Please verify the O365 properties.')

def get_access_token():
    account = get_or_set_account()
    token = account.connection.token_backend.get_token()
    if token is None:
        raise RuntimeError('Could not retrieve access token. Please ensure that the credentials are set correctly.')
    
    return token['access_token']

def create_subscription(mailbox):
    base_url = env('BASE_URL')
    token = get_access_token()
    expiration_time = datetime.datetime.now(tz=datetime.timezone.utc) + EXPIRATION_DURATION
    cert = PEM_DATA.decode().replace('\r\n', '').replace('-----BEGIN CERTIFICATE-----','').replace('-----END CERTIFICATE-----','')
    req_data = {
        'changeType': 'created,updated,deleted',
        'notificationUrl': f'{base_url}/api/subscriptions/',
        'resource': f'/users/{mailbox}/events?$select=id,iCalUId,isAllDay,recurrence,organizer,start,end,subject,type',
        'clientState': 'stateValue',
        'expirationDateTime': f'{expiration_time.isoformat()}',
        'includeResourceData': True,
        'encryptionCertificateId': '1',
        'encryptionCertificate': cert,
    }
    headers = {
        'Authorization': f'Bearer {token}',
    }

    response = requests.post(f'{GRAPH_URL}/subscriptions', json=req_data, headers=headers)
    response = response.json()

    if 'error' in response:
        raise RuntimeError(f'Subscription creation failed with code: {response["error"]["code"]} '
                            f'and message: {response["error"]["message"]}')
    subscription_details = {
        'subscription_id': response['id'],
        'expiration_time': expiration_time,
    }

    return subscription_details

def renew_subscription(subscription_id):
    token = get_access_token()
    expiration_time = datetime.datetime.now(tz=datetime.timezone.utc) + EXPIRATION_DURATION
    url = f'{GRAPH_URL}/subscriptions/{subscription_id}'
    req_data = {
        'expirationDateTime': f'{expiration_time.isoformat()}'
    }
    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = requests.patch(url, json=req_data, headers=headers)
    response = response.json()

    if 'error' in response:
        raise RuntimeError(f'Subscription creation failed with code: {response["error"]["code"]} '
                            f'and message: {response["error"]["message"]}')
    return expiration_time


def decrypt_message(data_key, signature, data):
    decoded_data = b64decode(data)
    cipher_rsa = PKCS1_OAEP.new(PRIVATE_KEY)

    sym_key = cipher_rsa.decrypt(b64decode(data_key))
    h = hmac.new(sym_key, msg=decoded_data, digestmod=hashlib.sha256)
    sig_test = b64encode(h.digest()).decode()

    if sig_test == signature:
        iv = sym_key[:16]
        cipher_aes = AES.new(sym_key, AES.MODE_CBC, iv=iv)
        decrypted_data = cipher_aes.decrypt(decoded_data)

        # Remove trailing characters due to the block size
        decrypted_str = decrypted_data.decode('utf-8')
        decrypted_str = decrypted_str[:-ord(decrypted_str[len(decrypted_str)-1:])]
        data_obj = json.loads(decrypted_str)

        return data_obj
    else:
        raise ValueError('Could not decrypt the payload. Please verify the data')

def create_exchange_event(event_details, room_resource):
    token = get_access_token()
    url = f'{GRAPH_URL}/users/{room_resource.email}/calendar/events'
    
    headers = {
        'Authorization': f'Bearer {token}'
    }
    payload = {
        'subject': event_details['subject'],
        'start': {
            'dateTime': event_details['start_time'].isoformat(),
            'timeZone': settings.TIME_ZONE
        },
        'end': {
            'dateTime': event_details['end_time'].isoformat(),
            'timeZone': settings.TIME_ZONE
        },
        'location': {
            'locationType': 'default',
            'locationEmailAddress': room_resource.email,
            'displayName': room_resource.name
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    response = response.json()

    if 'error' in response:
        raise RuntimeError(f'Event creation failed with code: {response["error"]["code"]} '
                            f'and message: {response["error"]["message"]}')
    return response