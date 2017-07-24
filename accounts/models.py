# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.db import models


def user_is_authentificated(user):
    return user is not None


class UserManager(BaseUserManager):

    def create_user(self, email, password=None):
        if not email:
            raise ValueError("Please provide email address")

        user = self.model(
            email=UserManager.normalize_email(email),
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        user = self.create_user(
            email,
            password=password,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    ROLE_CHOICES = (
        ('admin', 'admin'),
        ('user', 'user')
    )

    class Meta:
        db_table = 'users'

    email = models.EmailField(
        max_length=255,
        blank=False,
        null=False,
        unique=True
    )
    first_name = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    last_name = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    middle_name = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    created_datetime = models.DateTimeField(
        auto_now_add=True
    )
    last_login_ip = models.GenericIPAddressField(
        blank=True,
        null=True
    )
    is_active = models.BooleanField(
        default=True
    )
    is_admin = models.BooleanField(
        default=False
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='user'
    )

    def __unicode__(self):
        return self.email

    def get_full_name(self):
        return self.email

    def get_short_name(self):
        return self.email

    @property
    def is_staff(self):
        return self.is_admin

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True
