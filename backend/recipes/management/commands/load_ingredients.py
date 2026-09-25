from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from foodgram.constants import INGREDIENTS_CSV_RELATIVE_PATH
from recipes.models import Ingredient

INGREDIENTS_PATHS = (
    Path(settings.BASE_DIR) / INGREDIENTS_CSV_RELATIVE_PATH,
    Path(settings.BASE_DIR).parent / INGREDIENTS_CSV_RELATIVE_PATH,
)


class Command(BaseCommand):
    help = 'Загружает ингредиенты из data/ingredients.csv'

    def handle(self, *args, **options):
        csv_path = None
        for candidate in INGREDIENTS_PATHS:
            if candidate.exists():
                csv_path = candidate
                break

        if csv_path is None:
            self.stderr.write('Файл ingredients.csv не найден')
            return

        ingredients = []
        existing = set(
            Ingredient.objects.values_list('name', 'measurement_unit')
        )
        for line in csv_path.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line:
                continue
            name, unit = line.rsplit(',', 1)
            if (name, unit) in existing:
                continue
            ingredients.append(
                Ingredient(name=name, measurement_unit=unit)
            )
            existing.add((name, unit))

        created = Ingredient.objects.bulk_create(ingredients)
        self.stdout.write(
            self.style.SUCCESS(
                f'Загружено ингредиентов: {len(created)}'
            )
        )
