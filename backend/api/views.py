from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework import status
from rest_framework.response import Response
from djoser.views import UserViewSet as DjoserUserViewSet

from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAdminOrReadOnly, IsAuthorOrAdminOrReadOnly
from .serializers import (
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeShortSerializer,
    RecipeWriteSerializer,
    TagSerializer,
    SubscriptionSerializer,
)
from .utils import decode_base36, encode_base36
from users.models import Subscription


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
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if not relation_queryset.exists():
            raise ValidationError('Recipe does not exist')
        relation_queryset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

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

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__in_shopping_cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        )

        lines = []
        for ingredient in ingredients:
            lines.append(
                f"{ingredient['ingredient__name']} "
                f"({ingredient['ingredient__measurement_unit']}) — "
                f"{ingredient['total_amount']}"
            )
        content = '\n'.join(lines)
        response = HttpResponse(
            content,
            content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )

        return response

def redirect_short_link(request, short_code):
    recipe_id = decode_base36(short_code)
    recipe = get_object_or_404(
        Recipe,
        id=recipe_id
    )
    return redirect(f'/recipes/{recipe.id}/')


class UserViewSet(DjoserUserViewSet):
    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, pk=None):
        user = request.user
        author = self.get_object()
        if user == author:
            raise ValidationError('You can’t subscribe to yourself')
        subscription = Subscription.objects.filter(
            user=user,
            author=author
        )

        if self.request.method == 'POST':
            if subscription.exists():
                raise ValidationError('Subscription already exists')
            Subscription.objects.create(
                user=user,
                author=author
            )
            serializer = SubscriptionSerializer(
                author,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if not subscription.exists():
            raise ValidationError('Subscription does not exist')
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        authors_ids = Subscription.objects.filter(
            user=request.user
        ).values_list('author_id', flat=True)

        authors = User.objects.filter(id__in=authors_ids)
        page = self.paginate_queryset(authors)
        serializer = SubscriptionSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)