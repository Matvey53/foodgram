from rest_framework import viewsets 
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend

from recipes.models import Tag, Ingredient, Recipe, Favorite, ShoppingCart
from .serializers import TagSerializer, IngredientSerializer, RecipeReadSerializer, RecipeWriteSerializer, RecipeShortSerializer
from .permissions import IsAdminOrReadOnly, IsAuthorOrAdminOrReadOnly
from .filters import IngredientFilter, RecipeFilter


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
        object_model = model.objects.filter(
            user=user,
            recipe=recipe
        )
        if self.request.method == 'POST':
            if object_model.exists():
                raise ValidationError(f'Recipe already exists in {model}')
            model.objects.create(
                user=user,
                recipe=recipe
            )
            serializer = RecipeShortSerializer(recipe)
            return Response(serializer.data, status=201)
        if not object_model.exists():
            raise ValidationError(f'Recipe does not exists in {model}')
        object_model.delete()
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

        