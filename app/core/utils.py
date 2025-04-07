import uuid
import os


from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.models import Recipe


def recipe_image_file_path(instance: Optional['Recipe'], filename: str):
    """Generate file path for new recipe image."""
    if instance is None:
        raise ValueError('instance is None')

    (_, ext) = os.path.splitext(filename)
    filename = f'{uuid.uuid4()}{ext}'
    return os.path.join('uploads', 'recipe', str(instance.id), filename)


def post_content_file_path(instance: Optional['Recipe'], filename: str):
    """Generate file path for new post content."""
    if instance is None:
        raise ValueError('instance is None')

    (_, ext) = os.path.splitext(filename)
    filename = f'{uuid.uuid4()}{ext}'
    return (
        os.path.join('uploads', 'post', str(
            instance.id), 'content_file', filename)
    )
