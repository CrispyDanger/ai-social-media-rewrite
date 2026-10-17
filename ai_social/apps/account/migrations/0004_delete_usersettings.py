from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user_account', '0003_usersettings'),
    ]

    operations = [
        migrations.DeleteModel(
            name='UserSettings',
        ),
    ]
