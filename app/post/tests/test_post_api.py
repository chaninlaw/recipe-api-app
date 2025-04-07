"""
Tests for the post app.
"""
import os
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from django.test import TestCase

from core.models import Post
from post import serializers


POST_URL = reverse('post:post-list')


def create_test_user(email='user@exmaple.com', password='testpass'):
    """Create a sample user."""
    return get_user_model().objects.create_user(email, password)


def create_test_content():
    """Create and return a sample content."""
    return {
        'schema_version': 0,
        'delta': [
            {'insert': 'Hello, world!'},
            {'attributes': {'bold': True}, 'insert': 'Bold text'},
            {'insert': '\n'}
        ],
    }


def create_test_post(author, **params):
    """Create and return a sample post."""
    defaults = {
        'title': 'Sample Post',
        'content': create_test_content(),
    }
    defaults.update(params)

    return Post.objects.create(author=author, **defaults)


class PublicPostAPITests(TestCase):
    """Test the unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving post.."""
        res = self.client.get(POST_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivatePostAPITests(TestCase):
    """Test the authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_posts(self):
        """Test retrieving a list of posts."""
        create_test_post(author=self.user)

        res = self.client.get(POST_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        posts = Post.objects.all().order_by('-created_at')
        serializer = serializers.PostSerializer(posts, many=True)
        self.assertEqual(res.data, serializer.data)

    def test_get_post_detail(self):
        """Test retrieving a post detail."""
        post = create_test_post(author=self.user)
        url = reverse('post:post-detail', args=[post.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        serializer = serializers.PostSerializer(post)
        self.assertEqual(res.data, serializer.data)

    def test_create_post(self):
        """Test creating a new post."""
        payload = {
            'title': 'New Post',
            'content': create_test_content(),
        }
        res = self.client.post(POST_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        post = Post.objects.get(id=res.data['id'])
        for key, value in payload.items():
            self.assertEqual(getattr(post, key), value)
        self.assertEqual(post.author, self.user)

    def test_partial_update_post(self):
        """Test updating a post with PATCH."""
        original_post = create_test_post(author=self.user)
        payload = {
            'title': 'Updated Post',
            'content': create_test_content(),
        }
        url = reverse('post:post-detail', args=[original_post.id])
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        original_post.refresh_from_db()
        self.assertEqual(original_post.title, payload['title'])
        self.assertEqual(original_post.content, payload['content'])

    def test_full_update_post(self):
        """Test updating a post with PUT."""
        original_post = create_test_post(author=self.user)
        payload = {
            'title': 'Updated Post',
            'content': create_test_content(),
        }
        url = reverse('post:post-detail', args=[original_post.id])
        res = self.client.put(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        original_post.refresh_from_db()
        self.assertEqual(original_post.title, payload['title'])
        self.assertEqual(original_post.content, payload['content'])

    def test_delete_post(self):
        """Test deleting a post."""
        post = create_test_post(author=self.user)
        url = reverse('post:post-detail', args=[post.id])
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        posts = Post.objects.filter(id=post.id)
        self.assertFalse(posts.exists())

    def test_create_post_with_invalid_content(self):
        """Test creating a post with invalid content."""
        payload = {
            'title': 'New Post',
            'content': {
                'schema_version': 0,
                'delta': 'Invalid data',
            },
            'invalid_field': 'Invalid data'
        }
        res = self.client.post(POST_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_post_with_empty_content(self):
        """Test creating a post with empty content."""
        payload = {
            'title': 'New Post',
            'content': {
                'schema_version': 0,
                'delta': [],
            }
        }
        res = self.client.post(POST_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)


class ImageUploadTests(TestCase):
    """Test image upload for post."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user()
        self.client.force_authenticate(user=self.user)

    def tearDown(self):
        """Clean up any uploaded files."""
        posts = Post.objects.all()
        for post in posts:
            for content_file in post.content_files.all():
                # Delete the physical file first if it exists
                if (
                    content_file.file and
                    hasattr(content_file.file, 'path') and
                    os.path.exists(content_file.file.path)
                ):
                    os.remove(content_file.file.path)
                # Then delete the database record
                content_file.delete()

    @patch('uuid.uuid4')
    def test_create_post_with_image(self, mock_uuid):
        """Test creating a post with image."""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        payload = {
            'title': 'New Post',
            'content': {
                'schema_version': 0,
                'delta': [
                    {'insert': {'image': 'https://picsum.photos/200'}}
                ],
            }
        }
        res = self.client.post(POST_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        post = Post.objects.get(id=res.data['id'])
        self.assertEqual(post.title, payload['title'])
        content_file = post.content_files.first()
        self.assertTrue(os.path.exists(content_file.file.path))
        self.assertEqual(
            content_file.file.url,
            res.data['content']['delta'][0]['insert']['image']
        )

    @patch('uuid.uuid4')
    def test_update_post_image(self, mock_uuid):
        """Test updating a post with image."""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        post = create_test_post(author=self.user)
        payload = {
            'title': 'Updated Post',
            'content': {
                'schema_version': 0,
                'delta': [
                    {'insert': {'image': 'https://picsum.photos/200'}}
                ],
            }
        }
        url = reverse('post:post-detail', args=[post.id])
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertEqual(post.title, payload['title'])
        content_file = post.content_files.first()
        self.assertTrue(os.path.exists(content_file.file.path))
        self.assertEqual(
            content_file.file.url,
            res.data['content']['delta'][0]['insert']['image']
        )

    def test_create_post_with_invalid_image(self):
        """Test creating a post with invalid image URL."""
        payload = {
            'title': 'New Post',
            'content': {
                'schema_version': 0,
                'delta': [
                    {'insert': {'image': 'invalid-url'}}
                ],
            }
        }
        res = self.client.post(POST_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        post = Post.objects.get(id=res.data['id'])
        self.assertFalse(bool(post.content_files.first()))
        self.assertEqual(
            'invalid-url',
            res.data['content']['delta'][0]['insert']['image']
        )
