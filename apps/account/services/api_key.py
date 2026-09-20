from apps.account.models import UserSettings


def get_openrouter_api_key(user):
    record = UserSettings.objects.filter(user=user).first()
    if record is None:
        return None
    return record.openrouter_api_key or None
