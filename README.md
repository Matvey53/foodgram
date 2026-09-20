# Foodgram

Сайт с рецептами: можно публиковать свои, подписываться на авторов, добавлять блюда в избранное и скачивать список покупок.

Стек: Python, Django, DRF, Djoser, PostgreSQL, Nginx, Docker. Фронтенд готовый, из Практикума.

## Запуск локально

Нужен PostgreSQL и файл `.env` в корне (есть пример в `.env.example`).

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py load_ingredients
python manage.py createsuperuser
python manage.py runserver
```

API: http://127.0.0.1:8000/api/  
Админка: http://127.0.0.1:8000/admin/

Документация: `docs/openapi-schema.yml`, на сайте — `/api/docs/`.

## Docker

Локально из исходников:

```bash
cd infra
docker compose up --build
```

На сервере образы с Docker Hub, файл `infra/docker-compose.production.yml`. В `~/foodgram/.env` должны быть IP сервера в `ALLOWED_HOSTS` и `CSRF_TRUSTED_ORIGINS`.

Сайт: http://localhost  
Админка: http://localhost/admin/

Данные для ревью в `tests.yml`.

При пуше в `main` GitHub Actions гоняет flake8, собирает образы и деплоит. Секреты репозитория: `DOCKER_USERNAME`, `DOCKER_PASSWORD`, `HOST`, `USER`, `SSH_KEY`.

## Автор

[Matvey Vlasov](https://github.com/Matvey53)
