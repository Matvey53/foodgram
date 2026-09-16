from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает ингредиенты из data/ingredients.csv'

    def handle(self, *args, **options):
        csv_path = None
        for candidate in (
            Path(settings.BASE_DIR) / 'data' / 'ingredients.csv',
            Path(settings.BASE_DIR).parent / 'data' / 'ingredients.csv',
        ):
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
