from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAdminOrReadOnly, IsAuthorOrAdminOrReadOnly
from .serializers import (
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeShortSerializer,
    RecipeWriteSerializer,
    TagSerializer,
)
from .utils import decode_base36, encode_base36


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (
        IsAuthenticatedOrReadOnly,
        IsAuthorOrAdminOrReadOnly
    )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _change_relation(self, model):
        user = self.request.user
        recipe = self.get_object()
        relation_queryset = model.objects.filter(
            user=user,
            recipe=recipe
        )
        if self.request.method == 'POST':
            if relation_queryset.exists():
                raise ValidationError('Recipe already exists')
            model.objects.create(
                user=user,
                recipe=recipe
            )
            serializer = RecipeShortSerializer(recipe)
            return Response(serializer.data, status=201)
        if not relation_queryset.exists():
            raise ValidationError('Recipe does not exist')
        relation_queryset.delete()
        return Response(status=204)

    @action(
        detail=True,
        url_path='favorite',
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def add_recipe_to_favorite(self, request):
        return self._change_relation(Favorite)

    @action(
        detail=True,
        url_path='shopping_cart',
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def add_recipe_to_shopping_cart(self, request):
        return self._change_relation(ShoppingCart)

    @action(detail=True, url_path='get-link')
    def create_short_link(self, request):
        recipe = self.get_object()
        short_code = encode_base36(recipe.id)
        uri = request.build_absolute_uri(f'/s/{short_code}/')
        return Response(
            {"short-link": uri}
        )


def redirect_short_link(request, short_code):
    recipe_id = decode_base36(short_code)
    recipe = get_object_or_404(
        Recipe,
        id=recipe_id
    )
    return redirect(f'/recipes/{recipe.id}/')
