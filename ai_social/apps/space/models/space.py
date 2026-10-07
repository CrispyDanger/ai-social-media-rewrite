from django.conf import settings
from django.db import models
from django.db.models import Count, Exists, OuterRef, QuerySet
from django.db.models.functions import Lower


class SpaceQuerySet(QuerySet):
    def visible_to(self, user):
        is_member = self.model.members.through.objects.filter(
            space_id=OuterRef('pk'),
            user=user,
        )
        return self.filter(Exists(is_member))

    def with_member_count(self):
        return self.annotate(member_count=Count('memberships'))


class Space(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    description = models.CharField(max_length=160, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_spaces',
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='Membership',
        related_name='spaces',
        blank=True,
    )

    objects = SpaceQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower('slug'),
                name='space_slug_ci_unique',
            ),
        ]

    def __str__(self):
        return self.name
