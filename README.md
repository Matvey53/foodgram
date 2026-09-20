# Foodgram

Сайт с рецептами: можно публиковать свои, подписываться на авторов, добавлять блюда в избранное и скачивать список покупок.

Стек: Python, Django, DRF, Djoser, PostgreSQL, Nginx, Docker.

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

## Основные эндпоинты

| Метод | URL | Описание |
| --- | --- | --- |
| POST | `/api/users/` | Регистрация |
| POST | `/api/auth/token/login/` | Получение токена |
| GET | `/api/recipes/` | Список рецептов |
| POST | `/api/recipes/` | Создание рецепта |
| GET | `/api/recipes/download_shopping_cart/` | Скачать список покупок |

## Автор

[Matvey Vlasov](https://github.com/Matvey53)
