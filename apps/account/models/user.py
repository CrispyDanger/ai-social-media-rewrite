from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _


HANDLE_VALIDATOR = RegexValidator(
    regex=r'^[A-Za-z0-9_]{1,15}$',
    message=_(
        'Enter a valid handle. 1–15 characters: letters, numbers, and underscores only.'
    ),
)


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, username, password, extra_fields)

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        self._validate_superuser_flags(extra_fields)
        return self._create_user(email, username, password, extra_fields)

    def _create_user(self, email, username, password, extra_fields):
        self._validate_identity(email, username)
        user = self.model(
            email=self.normalize_email(email),
            username=username,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def _validate_identity(self, email, username):
        if not email:
            raise ValueError('Email is required.')
        if not username:
            raise ValueError('Username is required.')

    def _validate_superuser_flags(self, extra_fields):
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')


class User(AbstractUser):
    username = models.CharField(
        _('username'),
        max_length=15,
        unique=True,
        help_text=_(
            'Required. 15 characters or fewer. Letters, digits, and underscores only.'
        ),
        validators=[HANDLE_VALIDATOR],
        error_messages={
            'unique': _('A user with that username already exists.'),
        },
    )
    email = models.EmailField(_('email address'), unique=True)
    display_name = models.CharField(max_length=50)
    is_verified = models.BooleanField(default=False)
    following = models.ManyToManyField(
        'self',
        through='Follow',
        through_fields=('follower', 'following'),
        related_name='followers',
        symmetrical=False,
        blank=True,
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'display_name']

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower('username'),
                name='user_account_username_ci_unique',
            ),
        ]

    def __str__(self):
        return self.username
