import os
from io import BytesIO

import django
from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foodgram.settings')
django.setup()

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import User


def make_image(color, title):
    image = Image.new('RGB', (640, 480), color)
    draw = ImageDraw.Draw(image)
    draw.rectangle((24, 24, 616, 456), outline=(255, 255, 255), width=4)
    draw.text((40, 210), title, fill=(255, 255, 255))
    buffer = BytesIO()
    image.save(buffer, format='JPEG', quality=85)
    buffer.seek(0)
    slug = ''.join(char if char.isalnum() else '_' for char in title)
    return ContentFile(buffer.read(), name=f'{slug}.jpg')


def upsert_user(email, username, password, first_name, last_name, superuser=False):
    user = User.objects.filter(email=email).first()
    if user is None:
        user = User.objects.filter(username=username).first()
    if user is None:
        create = (
            User.objects.create_superuser
            if superuser
            else User.objects.create_user
        )
        return create(
            email=email,
            password=password,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
    user.email = email
    user.username = username
    user.first_name = first_name
    user.last_name = last_name
    user.set_password(password)
    if superuser:
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
    user.save()
    return user


def get_or_create_tag(name, slug):
    tag, _ = Tag.objects.get_or_create(slug=slug, defaults={'name': name})
    return tag


def get_ingredient(name):
    ingredient = Ingredient.objects.filter(name__iexact=name).first()
    if ingredient is None:
        ingredient = Ingredient.objects.filter(name__icontains=name).first()
    if ingredient is None:
        raise RuntimeError(f'Ингредиент не найден: {name}')
    return ingredient


def upsert_recipe(author, name, text, cooking_time, color, tags, ingredients):
    recipe = Recipe.objects.filter(author=author, name=name).first()
    if recipe is None:
        recipe = Recipe(author=author, name=name)
    recipe.text = text
    recipe.cooking_time = cooking_time
    recipe.image.save(f'{recipe.name}.jpg', make_image(color, name), save=False)
    recipe.save()
    recipe.tags.set(tags)
    recipe.recipeingredients.all().delete()
    RecipeIngredient.objects.bulk_create(
        RecipeIngredient(
            recipe=recipe,
            ingredient=get_ingredient(item_name),
            amount=amount,
        )
        for item_name, amount in ingredients
    )
    return recipe


review = upsert_user(
    email='review@admin.ru',
    username='review',
    password='review1admin',
    first_name='Игорь',
    last_name='Ревьюер',
    superuser=True,
)
cook = upsert_user(
    email='cook@foodgram.ru',
    username='cook',
    password='cookpass123',
    first_name='Анна',
    last_name='Поварова',
)
baker = upsert_user(
    email='baker@foodgram.ru',
    username='baker',
    password='bakerpass123',
    first_name='Пётр',
    last_name='Пекарев',
)

breakfast = get_or_create_tag('Завтрак', 'breakfast')
lunch = get_or_create_tag('Обед', 'lunch')
dinner = get_or_create_tag('Ужин', 'dinner')

recipes = [
    upsert_recipe(
        review,
        'Борщ',
        'Классический борщ со свеклой, капустой и сметаной.',
        90,
        (140, 28, 28),
        [lunch, dinner],
        (('свекла', 300), ('капуста', 200), ('картофель', 250), ('морковь', 100)),
    ),
    upsert_recipe(
        review,
        'Оливье',
        'Праздничный салат с картофелем, яйцами и майонезом.',
        40,
        (70, 120, 50),
        [lunch],
        (('картофель', 400), ('яйца куриные', 4), ('морковь', 150), ('майонез', 100)),
    ),
    upsert_recipe(
        review,
        'Блины',
        'Тонкие блины на молоке к завтраку.',
        30,
        (200, 140, 40),
        [breakfast],
        (('мука', 250), ('молоко', 500), ('яйца куриные', 3), ('сахар', 30)),
    ),
    upsert_recipe(
        review,
        'Сырники',
        'Сырники из творога со сметаной.',
        25,
        (210, 170, 70),
        [breakfast],
        (('творог', 400), ('яйца куриные', 2), ('мука', 80), ('сахар', 40)),
    ),
    upsert_recipe(
        cook,
        'Паста карбонара',
        'Спагетти с яйцом, сыром и беконом.',
        25,
        (180, 150, 80),
        [dinner],
        (('макароны', 300), ('яйца куриные', 3), ('сыр', 80), ('бекон', 120)),
    ),
    upsert_recipe(
        cook,
        'Греческий салат',
        'Салат с помидорами, огурцами и сыром фета.',
        15,
        (40, 110, 50),
        [lunch, dinner],
        (('помидоры', 300), ('огурцы', 200), ('сыр', 150), ('оливковое масло', 30)),
    ),
    upsert_recipe(
        baker,
        'Шоколадный кекс',
        'Простой шоколадный кекс к чаю.',
        50,
        (70, 40, 30),
        [breakfast],
        (('мука', 200), ('сахар', 150), ('яйца куриные', 2), ('какао', 40)),
    ),
]

print('USERS')
for user in (review, cook, baker):
    print(
        user.username,
        user.email,
        'superuser' if user.is_superuser else 'user',
        f'recipes={user.recipes.count()}',
    )
print('RECIPES', Recipe.objects.count())
for recipe in Recipe.objects.order_by('id'):
    print(recipe.id, recipe.name, recipe.author.username)
print('TAGS', list(Tag.objects.values_list('name', flat=True)))
print('ALLOWED_HOSTS', list(settings.ALLOWED_HOSTS))
