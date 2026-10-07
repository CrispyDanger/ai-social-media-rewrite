from django.core.validators import FileExtensionValidator
from django.db import models

from .post import Post

IMAGE_EXTENSIONS = ['gif', 'jpeg', 'jpg', 'png', 'webp']
VIDEO_EXTENSIONS = ['mov', 'mp4', 'webm']


def media_upload_to(instance, filename):
    return f'posts/{instance.post_id}/{filename}'


class Media(models.Model):
    class MediaType(models.TextChoices):
        IMAGE = 'image', 'Image'
        VIDEO = 'video', 'Video'

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='media',
    )
    file = models.FileField(
        upload_to=media_upload_to,
        validators=[
            FileExtensionValidator(IMAGE_EXTENSIONS + VIDEO_EXTENSIONS),
        ],
    )
    media_type = models.CharField(max_length=5, choices=MediaType)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name_plural = 'media'

    def __str__(self):
        return f'{self.get_media_type_display()} for {self.post}'
