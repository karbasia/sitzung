# Sitzung

Sitzung is an open source room panel. The goal is to allow users to quickly book meetings via a mounted device with a browser. Sitzung will integrate directly with Microsoft 365 and utilizes subscriptions for receiving scheduling updates. It's currently a WIP and NOT production ready.

## Requirements

1. A Microsoft 365 Exchange instance
1. Microsoft Entra ID setup with the appropriate Graph permissions (guide coming soon)
1. Backend server must be accessible from the Microsoft 365 service
1. One or more touch-enabled devices with browsers (iPad, Pixel Tablet, Surface, etc)

## Architecture

Diagram TBD

## Development Quick Start

Rename `.env.template` to `.env` and enter the appropriate `BASE_URL`, `O365_*` values

Install dependencies `pip install -r requirements.txt`

Start the database and cache servers by running `docker compose up -d`

Run migrations `python manage.py migrate`

Set up the Django superuser using `python manage.py createsuperuser`

Generate a private key and certificate using the following command:
```
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -sha256 -days 365 -nodes \
-subj "/C=CA/ST=Ontario/L=Toronto/O=Karbasi/OU=DEV/CN=localhost"
```
NOTE: Keep `cert.pem` and `key.pem` in the project root folder. It will be used to sign the requests and decrypt the data from the subscriptions.

Now you can log into the admin interface and set up resources to test!


### Environment Variable Definitions

| Parameter | Description |
|---|---|
| DEBUG | Set to True for dev. Otherwise False |
| SECRET_KEY | Django secret key. Use a unique value for production |
| BASE_URL | The URL of the backend service. This must be accessible from Microsoft 365 |
| POSTGRES_HOST | Postgres hostname |
| POSTGRES_PORT | Postgres port |
| POSTGRES_DB | Postgres database name |
| POSTGRES_USER | Postgres username |
| POSTGRES_PASSWORD | Postgres password |
| CACHE_HOST | Memcached hostname |
| CACHE_PORT | Memcached port |
| O365_TENANT | Microsoft 365 application tenant ID |
| O365_CLIENT | Microsoft 365 client ID |
| O365_SECRET | Microsoft 365 secret |