"""
Tests for the delta serializer utility.
"""

from django.test import TestCase

from post.utils import QuillDeltaSerializer


class QuillDeltaSerializerTestsValid(TestCase):
    """Tests for valid data for the QuillDeltaSerializer."""

    def test_insert_oneline(self):
        data = {
            'delta': [
                {'insert': 'Hello, world!'}
            ],
        }
        serializer = QuillDeltaSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_insert_multiline(self):
        data = {
            'delta': [
                {'insert': 'Hello, world!\n'},
                {'insert': 'This is a test.\n'}
            ],
        }
        serializer = QuillDeltaSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_insert_with_attributes(self):
        data = {
            'delta': [
                {'insert': 'Hello, world!'},
                {'insert': 'This is a test.', 'attributes': {'bold': True}}
            ],
        }
        serializer = QuillDeltaSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_insert_with_html(self):
        data = {
            'delta': [
                {'insert': 'Hello, world!'},
                {'insert': 'This is a test.', 'attributes': {'bold': True}}
            ],
            'html': '<p>Hello, world!</p><p>This is a test.</p>'
        }
        serializer = QuillDeltaSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_empty_delta(self):
        data = {
            'delta': []
        }
        serializer = QuillDeltaSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_schema_version(self):
        data = {
            'schema_version': 1,
            'delta': [
                {'insert': 'Hello, world!'}
            ],
        }
        serializer = QuillDeltaSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_empty_attributes(self):
        data = {
            'delta': [
                {'insert': 'Hello, world!', 'attributes': {}}
            ],
        }
        serializer = QuillDeltaSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_insert_image(self):
        data = {
            'delta': [
                {'insert': {'image': 'http://example.com/image.png'}}
            ],
        }
        serializer = QuillDeltaSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_insert_video(self):
        data = {
            'delta': [
                {'insert': {'video': 'http://example.com/video.mp4'}}
            ]
        }
        serializer = QuillDeltaSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('delta', serializer.errors)
        self.assertIn('insert', serializer.errors['delta'][0])


class QuillDeltaSerializerTestsInvalidData(TestCase):
    """Tests for invalid data for the QuillDeltaSerializer."""

    def test_plain_str(self):
        data = {'delta': 'Hello, World!'}
        serializer = QuillDeltaSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_invalid_key_delta(self):
        data = {
            'delta': [
                {'insert': 'Hello, world!'},
                {'invalid_key': 'This should fail.'}
            ],
        }
        serializer = QuillDeltaSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('delta', serializer.errors)

    def test_missing_insert_key(self):
        data = {
            'delta': [
                {'attributes': {'bold': True}}
            ],
        }
        serializer = QuillDeltaSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('delta', serializer.errors)
