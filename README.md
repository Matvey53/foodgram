# Foodgram

Сервис для публикации рецептов: пользователи могут делиться рецептами, подписываться на авторов, добавлять блюда в избранное и формировать список покупок.

## Стек

- Python 3.12, Django, Django REST Framework, Djoser, Gunicorn
- PostgreSQL
- React (готовый фронтенд)
- Nginx, Docker, Docker Compose

## Переменные окружения

Скопируйте `.env.example` в `.env` в корне репозитория:

```
SECRET_KEY=...
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost,http://127.0.0.1
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram
POSTGRES_PASSWORD=foodgram
DB_HOST=localhost
DB_PORT=5432
```

На сервере укажите IP или домен в `ALLOWED_HOSTS` и `CSRF_TRUSTED_ORIGINS`.  
В Docker Compose хост БД подставляется автоматически (`db`).

## Локальный запуск бэкенда без Docker

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

Нужна локальная PostgreSQL с пользователем и базой из `.env`.

API: http://127.0.0.1:8000/api/  
Админка: http://127.0.0.1:8000/admin/

## Запуск в Docker

Локально, сборка из исходников:

```bash
cd infra
docker compose up --build
```

На сервере, образы с Docker Hub:

```bash
cd infra
docker compose -f docker-compose.production.yml up -d
```

Поднимаются PostgreSQL, Django+Gunicorn и Nginx. Контейнер frontend собирает статику и завершается.

- сайт: http://localhost
- API: http://localhost/api/
- админка: http://localhost/admin/
- документация: http://localhost/api/docs/

Админка: логин `admin`, пароль `admin` (см. `tests.yml`).

## CI / Docker Hub

При пуше в `main` GitHub Actions прогоняет тесты, собирает образы и выкладывает их на Docker Hub, затем деплоит на сервер. В секретах репозитория нужны:

- `DOCKER_USERNAME`
- `DOCKER_PASSWORD`
- `HOST` — публичный IP сервера (без `http://` и без порта)
- `USER` — linux-пользователь SSH на ВМ, обычно `ubuntu` (не логин GitHub)
- `SSH_KEY` — **приватный** ключ целиком, вместе со строками `BEGIN` и `END`
- `PASSPHRASE` — пароль ключа, если при `ssh-keygen` его задавали; иначе секрет можно не создавать

Если деплой падает с `ssh: unable to authenticate`, ключ на сервере не совпадает с секретом. На своей машине:

```bash
ssh-keygen -t ed25519 -f foodgram_deploy -N ""
```

Публичный ключ `foodgram_deploy.pub` добавьте на ВМ в `~/.ssh/authorized_keys` пользователя из секрета `USER`. Приватный ключ `foodgram_deploy` целиком вставьте в секрет `SSH_KEY`. Проверка с ноутбука:

```bash
ssh -i foodgram_deploy ubuntu@ВАШ_IP
```

После правки секретов достаточно Re-run failed jobs в Actions, новый коммит не обязателен.

Образы: `matvey53/foodgram_backend`, `matvey53/foodgram_frontend`, `matvey53/foodgram_nginx`.

На сервере в каталоге `foodgram` должен лежать `.env`. Файл `infra/docker-compose.production.yml` копируется туда автоматически.

## Основные эндпоинты

| Метод | URL | Описание |
| --- | --- | --- |
| POST | `/api/users/` | Регистрация |
| POST | `/api/auth/token/login/` | Получение токена |
| GET | `/api/recipes/` | Список рецептов |
| POST | `/api/recipes/` | Создание рецепта |
| GET | `/api/recipes/download_shopping_cart/` | Скачать список покупок |
| POST | `/api/users/{id}/subscribe/` | Подписка на автора |

Документация API: `docs/openapi-schema.yml` и коллекция `postman_collection/`.

## Автор

[Matvey Vlasov](https://github.com/Matvey53)

Дипломный проект Яндекс Практикума.
