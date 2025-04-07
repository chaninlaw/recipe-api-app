"""
Serializer for post app.
"""
# from typing import cast
from rest_framework import serializers

from core.models import Post
from post.utils import (QuillDeltaSerializer,
                        CreateUpdateFileQuillDeltaMixin)


class PostSerializer(CreateUpdateFileQuillDeltaMixin,
                     serializers.ModelSerializer[Post]):
    """Serializer for post objects."""

    content = QuillDeltaSerializer(file_field_name='content_files')

    class Meta:
        model = Post
        fields = ['id', 'title', 'content',
                  'author', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']
