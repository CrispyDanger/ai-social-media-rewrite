from django.db import models

from apps.core.crypto import decrypt, encrypt, is_encrypted


class EncryptedTextField(models.TextField):
    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if not value or is_encrypted(value):
            return value
        return encrypt(value)

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def to_python(self, value):
        if not value or not is_encrypted(value):
            return value
        return decrypt(value)

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        return self.get_prep_value(value) or ''
