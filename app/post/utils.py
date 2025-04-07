"""
Utility functions for the post app.
"""

import os
import uuid
import requests
import urllib.parse
import logging
from io import BytesIO
import html as html_escape

from typing import cast, Dict, List, Any

from django.db.models import Model
from django.core.files.base import ContentFile

from rest_framework import serializers
from rest_framework.fields import Field


logger = logging.getLogger(__name__)


def download_image_content(url):
    """
    Download image content from a URL and return it as bytes.
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        return BytesIO(response.content)
    except Exception as e:
        logger.error(f"Error downloading image from {url}: {str(e)}")
        return None


def render_delta_to_html(delta_ops: List[Dict[str, Any]]) -> str:
    """
    Simple function to render delta operations to HTML.
    This replaces the need for the quill-delta html package.

    Args:
        delta_ops: List of delta operations

    Returns:
        HTML string representing the delta operations
    """
    html = []
    for op in delta_ops:
        insert = op.get('insert')
        attributes = op.get('attributes', {})

        if not insert:
            continue

        if isinstance(insert, str):
            # Handle text inserts
            content = html_escape.escape(insert)

            # Apply basic formatting
            if attributes:
                if attributes.get('bold'):
                    content = f"<strong>{content}</strong>"
                if attributes.get('italic'):
                    content = f"<em>{content}</em>"
                if attributes.get('underline'):
                    content = f"<u>{content}</u>"
                if attributes.get('strike'):
                    content = f"<s>{content}</s>"
                if attributes.get('link'):
                    url = html_escape.escape(attributes.get('link'))
                    content = (
                        f'<a href="{url}" target="_blank" '
                        f'rel="noopener noreferrer">{content}</a>'
                    )

            html.append(content)
        elif isinstance(insert, dict):
            # Handle media inserts
            if 'image' in insert:
                img_url = html_escape.escape(insert['image'])
                html.append(f'<img src="{img_url}" alt="Embedded image"/>')

    return ''.join(html)


class TextOrMediaField(Field):
    """
    Custom field to accept either a string or a media.
    """

    def to_internal_value(self, data):
        if isinstance(data, str) or isinstance(data, dict):
            return data
        raise serializers.ValidationError(
            "This field must be a string or a dictionary.")

    def to_representation(self, value):
        return value


class DeltaOpsSerializer(serializers.Serializer):
    """
    Serializer for delta operations.
    """
    insert = TextOrMediaField(required=True)
    attributes = serializers.DictField(required=False)

    class Meta:
        fields = ['insert', 'attributes']

    def validate_insert(self, value):
        """
        Validate the insert field.
        """
        DISALLOWED_MEDIA_TYPES = ['video']

        # Check if this is a dictionary with any forbidden media keys
        contains_forbidden_media = (
            isinstance(value, dict) and
            any(media_type in value.keys()
                for media_type in DISALLOWED_MEDIA_TYPES)
        )

        if contains_forbidden_media:
            raise serializers.ValidationError(
                f"Insert of {', '.join(DISALLOWED_MEDIA_TYPES)} "
                "is not allowed."
            )

        return value


class QuillDeltaSerializer(serializers.Serializer):
    """
    Serializer for quill delta format.
    This serializer handles the conversion of delta operations
    and the processing of image URLs.
    """
    schema_version = serializers.IntegerField(default=0, required=False)
    delta = DeltaOpsSerializer(many=True, default=list)

    class Meta:
        fields = ['schema_version', 'delta']

    def __init__(self, *args, **kwargs):
        self.file_field_name = kwargs.pop('file_field_name', None)
        super().__init__(*args, **kwargs)

    def __str__(self):
        return f'quill_delta_serializer: {self.file_field_name}'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['html'] = render_delta_to_html(data['delta'])
        return data

    def _process_files(self, instance: Model, delta: DeltaOpsSerializer):
        """Process files in the delta content."""
        if not self.file_field_name or not instance:
            return False

        is_modified = False
        for op in delta:
            insert = op.get('insert')
            if not self._is_insert_image(insert):
                continue

            image_url = op['insert']['image']
            if not self._is_valid_insert_image_url(image_url):
                continue

            # Process image and update the op
            try:
                # Download and save image
                content_bytes = download_image_content(image_url)
                if not content_bytes:
                    continue

                # Create a unique filename and path for the image
                path = self._get_path(image_url)

                # Check if the field is a ManyToManyField or FileField
                field = instance._meta.get_field(self.file_field_name)
                if field.many_to_many:
                    # Handle ManyToManyField
                    file_model = field.related_model
                    new_file = file_model.objects.create()
                    new_file.file.save(
                        path, ContentFile(content_bytes.getvalue()), save=True
                    )
                    getattr(instance, self.file_field_name).add(new_file)
                else:
                    # Handle FileField
                    file_field = getattr(instance, self.file_field_name)
                    file_field.save(
                        path, ContentFile(content_bytes.getvalue()), save=True
                    )

                # Update content with new URL
                op['insert']['image'] = (
                    new_file.file.url if field.many_to_many else file_field.url
                )
                is_modified = True
            except Exception as e:
                logger.error(
                    f"Error processing image after creation: {str(e)}")

        return is_modified

    def _get_path(self, image_url: str):
        """
        Get the path for the image.
        """
        _, ext = os.path.splitext(os.path.basename(
            urllib.parse.urlparse(image_url).path))

        unique_filename = f"{uuid.uuid4()}{ext or '.jpg'}"

        return f"post_images/{unique_filename}"

    def _is_insert_image(self, insert):
        """
        Check if the insert is an image.
        """
        return (
            isinstance(insert, dict) and
            'image' in insert and
            isinstance(insert['image'], str)
        )

    def _is_valid_insert_image_url(self, url):
        """
        Check if the URL is valid for image insertion.
        """
        return (
            isinstance(url, str) and
            url.startswith(('http://', 'https://'))
        )


class CreateFileQuillDeltaMixin:
    """
    Mixin for processing Quill Delta content with file uploads.

    This mixin should be used with ModelSerializer and placed
    before ModelSerializer in the inheritance chain:

    class MySerializer(CreateFileQuillDeltaMixin, serializers.ModelSerializer):
        ...
    """

    def create(self, validated_data):
        instance = super().create(validated_data)
        self.perform_create_file(instance, validated_data)
        return instance

    def perform_create_file(self, instance: Model, validated_data):
        """Perform the creation of a file"""
        field_name, field = next(
            ((name, f) for name, f in self.fields.items()
             if isinstance(f, QuillDeltaSerializer)),
            (None, None)
        )

        if not field_name or not field:
            return instance

        typed_field = cast(QuillDeltaSerializer, field)
        if not hasattr(typed_field, 'file_field_name'):
            return instance

        delta_data = validated_data.get(field_name, {}).get('delta', [])
        is_modified = typed_field._process_files(instance, delta_data)
        if is_modified:
            instance.save()
        return instance


class UpdateFileQuillDeltaMixin:
    """
    Mixin for processing Quill Delta content with file uploads during updates.

    This mixin should be used with ModelSerializer and placed
    before ModelSerializer in the inheritance chain:

    class MySerializer(UpdateFileQuillDeltaMixin, serializers.ModelSerializer):
        ...
    """

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        self.perform_update_file(instance, validated_data)
        return instance

    def perform_update_file(self, instance, validated_data):
        """Perform the update of files"""
        field_name, field = next(
            ((name, f) for name, f in self.fields.items()
             if isinstance(f, QuillDeltaSerializer)),
            (None, None)
        )

        if not field_name or not field:
            return instance

        typed_field = cast(QuillDeltaSerializer, field)
        if not hasattr(typed_field, 'file_field_name'):
            return instance

        delta_data = validated_data.get(field_name, {}).get('delta', [])
        is_modified = typed_field._process_files(instance, delta_data)
        if is_modified:
            instance.save()
        return instance


class CreateUpdateFileQuillDeltaMixin(
    CreateFileQuillDeltaMixin,
    UpdateFileQuillDeltaMixin
):
    """
    Mixin for processing Quill Delta content with file uploads during creation
    and updates.

    This mixin should be used with ModelSerializer and placed
    before ModelSerializer in the inheritance chain:

    class MySerializer(CreateUpdateFileQuillDeltaMixin,
                       serializers.ModelSerializer):
        ...
    """
