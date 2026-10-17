from django.test import SimpleTestCase

from apps.bots.services.targeting.mentions import extract_handles


class ExtractHandlesTests(SimpleTestCase):
    def test_extracts_lowercased_unique_handles(self):
        self.assertEqual(extract_handles('hi @Alice and @bob_1, @alice!'), {'alice', 'bob_1'})

    def test_ignores_emails_and_overlong_handles(self):
        self.assertEqual(extract_handles('mail me@example.com or @abcdefghijklmnopq'), set())

    def test_no_mentions(self):
        self.assertEqual(extract_handles('just a post'), set())
