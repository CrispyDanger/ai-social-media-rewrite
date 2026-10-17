import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bots', '0001_initial'),
        ('space', '0002_invite'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='botpersona',
            name='name',
            field=models.CharField(max_length=50),
        ),
        migrations.AddField(
            model_name='botpersona',
            name='owner',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='owned_bot_personas',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='botpersona',
            name='space',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='bot_personas',
                to='space.space',
            ),
        ),
        migrations.AddIndex(
            model_name='botpersona',
            index=models.Index(fields=['space', 'owner'], name='bots_space_owner_idx'),
        ),
    ]
