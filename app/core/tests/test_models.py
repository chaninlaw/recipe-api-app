"""
Tests for models.
"""
from unittest.mock import patch
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models, utils


def create_test_user(**params) -> models.User:
    """Create a sample user."""
    default = {
        'email': 'test@example.com',
        'password': 'testpass123'
    }
    default.update(params)
    return get_user_model().objects.create_user(**default)


class ModelTests(TestCase):
    """Test models."""

    def test_create_user_with_email_successful(self):
        """Test creating a user with an email is successful."""
        email = 'test@example.com'
        password = 'testpass123'
        user = create_test_user(email=email, password=password)

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test email is normalized for new users."""
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.COM', 'TEST3@example.com'],
            ['test4@example.COM', 'test4@example.com'],
        ]

        for email, expected in sample_emails:
            user: models.User = create_test_user(
                email=email,
                password='sample123'
            )
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """Test creating user without an email raises error."""
        with self.assertRaises(ValueError):
            create_test_user(
                email=None,
                password='sample123'
            )

    def test_create_superuser(self):
        """Test creating a superuser."""
        email = "superuser@example.com"
        user: models.User = get_user_model().objects.create_superuser(
            email=email,
            password="superpass123",
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_active)

    def test_create_recipe(self):
        """Test creating a recipe is successful."""
        user = create_test_user(
            email='test@example.com',
            password='testpass123',
        )

        recipe = models.Recipe.objects.create(
            user=user,
            title='Sample Recipe',
            time_minutes=5,
            price=Decimal('5.50'),
            description='Sample recipe description',
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        """Test creating a tag is successful."""
        user = create_test_user()
        tag = models.Tag.objects.create(
            user=user,
            name='Sample Tag',
        )

        self.assertEqual(str(tag), tag.name)

    def test_create_ingredient(self):
        """Test creating an ingredient is successful."""
        user = create_test_user()
        ingredient = models.Ingredient.objects.create(
            user=user,
            name='Sample Ingredient',
        )

        self.assertEqual(str(ingredient), ingredient.name)

    @patch('uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        """Test generating image path."""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        recipe = models.Recipe.objects.create(
            user=create_test_user(),
            title='Sample Recipe',
            time_minutes=5,
            price=Decimal('5.50'),
            description='Sample recipe description',
        )
        file_path = utils.recipe_image_file_path(recipe, 'example.jpg')

        self.assertEqual(file_path, f'uploads/recipe/{recipe.id}/{uuid}.jpg')

    def test_create_post(self):
        """Test creating a post is successful."""

        user = create_test_user()
        post = models.Post.objects.create(
            author=user,
            title='Sample Post',
            content='Sample post content',
        )

        self.assertEqual(str(post), post.title)
