from django.test import SimpleTestCase
from pydantic import ValidationError

from apps.bots.services.generation.schemas import NewPost, Reply


class SchemaTests(SimpleTestCase):
    def test_text_up_to_limit_is_valid(self):
        self.assertEqual(len(NewPost(text='a' * 280).text), 280)

    def test_text_over_limit_is_rejected(self):
        for schema in (NewPost, Reply):
            with self.subTest(schema=schema.__name__), self.assertRaises(ValidationError):
                schema(text='a' * 281)

    def test_empty_text_is_rejected(self):
        with self.assertRaises(ValidationError):
            Reply(text='')
