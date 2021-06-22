from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager as Django_UserManager
from django.utils import timezone


class User(AbstractUser):
    page_claim_count = models.BigIntegerField(default=0)
    total_claim_count = models.BigIntegerField(default=0)
    annotation_count = models.BigIntegerField(default=0)
    label_count = models.BigIntegerField(default=0)

    def __str__(self):
        return self.username


class UserManager(Django_UserManager):

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """
        Creates and saves a User with the given username, email and password.
        """
        now = timezone.now()
        if not username:
            raise ValueError('The given username must be set')
        email = UserManager.normalize_email(email)
        user = User(username=username, email=email,
                    is_staff=True, is_active=True, is_superuser=True,
                    last_login=now, date_joined=now)

        user.set_password(password)
        user.save(using=self._db)
