import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('post', '0003_media'),
        ('space', '0002_invite'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='space',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='posts',
                to='space.space',
            ),
        ),
        migrations.AddIndex(
            model_name='post',
            index=models.Index(
                fields=['space', '-created_at'],
                name='post_space_created_idx',
            ),
        ),
    ]
