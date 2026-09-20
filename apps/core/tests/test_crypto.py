from django.test import SimpleTestCase

from apps.core.crypto import decrypt, encrypt, is_encrypted


class CryptoTests(SimpleTestCase):
    def test_encrypt_roundtrip(self):
        token = encrypt('sk-or-v1-secret')
        self.assertTrue(is_encrypted(token))
        self.assertNotEqual(token, 'sk-or-v1-secret')
        self.assertEqual(decrypt(token), 'sk-or-v1-secret')

    def test_empty_values_pass_through(self):
        self.assertEqual(encrypt(''), '')
        self.assertEqual(decrypt(''), '')
