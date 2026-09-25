from io import BytesIO

from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import FoodgramPagination
from api.permissions import IsAuthorOrAdminOrReadOnly
from api.serializers import (
    AvatarSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeShortSerializer,
    RecipeWriteSerializer,
    SubscriptionSerializer,
    TagSerializer,
)
from api.utils import decode_base36, encode_base36
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Subscription, User


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (AllowAny,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = (AllowAny,)
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
                raise ValidationError('Рецепт уже добавлен')
            model.objects.create(
                user=user,
                recipe=recipe
            )
            serializer = RecipeShortSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if not relation_queryset.exists():
            raise ValidationError('Рецепта нет в списке')
        relation_queryset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        url_path='favorite',
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def add_recipe_to_favorite(self, request, **kwargs):
        return self._change_relation(Favorite)

    @action(
        detail=True,
        url_path='shopping_cart',
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def add_recipe_to_shopping_cart(self, request, **kwargs):
        return self._change_relation(ShoppingCart)

    @action(detail=True, url_path='get-link')
    def create_short_link(self, request, **kwargs):
        recipe = self.get_object()
        short_code = encode_base36(recipe.id)
        uri = request.build_absolute_uri(
            reverse('short-link', args=[short_code])
        )
        return Response(
            {'short-link': uri}
        )

    def get_shopping_cart_ingredients(self, user):
        return RecipeIngredient.objects.filter(
            recipe__shoppingcarts__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')

    def build_shopping_cart_file(self, ingredients):
        lines = [
            f"{item['ingredient__name']} "
            f"({item['ingredient__measurement_unit']}) — "
            f"{item['total_amount']}"
            for item in ingredients
        ]
        content = '\n'.join(lines)
        return FileResponse(
            BytesIO(content.encode('utf-8')),
            as_attachment=True,
            filename='shopping_list.txt',
            content_type='text/plain; charset=utf-8'
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        ingredients = self.get_shopping_cart_ingredients(request.user)
        return self.build_shopping_cart_file(ingredients)


def redirect_short_link(request, short_code):
    recipe_id = decode_base36(short_code)
    recipe = get_object_or_404(
        Recipe,
        id=recipe_id
    )
    return redirect(f'/recipes/{recipe.id}/')


class UserViewSet(DjoserUserViewSet):
    pagination_class = FoodgramPagination

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return (AllowAny(),)
        return super().get_permissions()

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, **kwargs):
        user = request.user
        author = self.get_object()
        if user == author:
            raise ValidationError('Нельзя подписаться на самого себя')
        subscription = Subscription.objects.filter(
            user=user,
            author=author
        )

        if self.request.method == 'POST':
            if subscription.exists():
                raise ValidationError('Вы уже подписаны на этого пользователя')
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
            raise ValidationError('Подписки не существует')
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        authors = User.objects.filter(subscribers__user=request.user)
        page = self.paginate_queryset(authors)
        serializer = SubscriptionSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
        permission_classes=(IsAuthenticated,),
    )
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            serializer = AvatarSerializer(
                user,
                data=request.data
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )
        user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)
