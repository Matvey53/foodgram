from django_filters.rest_framework import (
    AllValuesMultipleFilter,
    BooleanFilter,
    CharFilter,
    FilterSet,
)

from recipes.models import Ingredient, Recipe


class RecipeFilter(FilterSet):
    tags = AllValuesMultipleFilter(
        field_name='tags__slug',
        distinct=True
    )
    is_favorited = BooleanFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = (
            'author',
            'tags',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user

        if value and user.is_authenticated:
            return queryset.filter(
                favorites__user=user
            )
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user

        if value and user.is_authenticated:
            return queryset.filter(
                shoppingcarts__user=user
            )
        return queryset


class IngredientFilter(FilterSet):
    name = CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ('name',)
