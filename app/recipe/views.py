"""
Views for the recipe APIs.
"""

from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Ingredient, Recipe, Tag
from recipe import serializers


class RecipeViewSet(viewsets.ModelViewSet):
    """Viewset for managing recipe APIs."""

    # Most of the action will only change a recipe detail, so
    # detail serializer is used
    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve the recipes for autenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == 'list':
            return serializers.RecipeSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new recipe."""
        serializer.save(user=self.request.user)


class TagViewSet(
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """Viewset for managing tags APIs."""
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter queryset the tags for authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-name')


class IngredientViewSet(
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """Viewset for managing ingredients APIs."""
    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter queryset the ingredients for authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-name')
