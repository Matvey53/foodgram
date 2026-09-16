from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
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

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Subscription, User

from .filters import IngredientFilter, RecipeFilter
from .pagination import FoodgramPagination
from .permissions import IsAuthorOrAdminOrReadOnly
from .serializers import (
    AvatarSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeShortSerializer,
    RecipeWriteSerializer,
    SubscriptionSerializer,
    TagSerializer,
)
from .utils import decode_base36, encode_base36


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
        uri = request.build_absolute_uri(f'/s/{short_code}/')
        return Response(
            {"short-link": uri}
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__in_shopping_carts__user=request.user
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
