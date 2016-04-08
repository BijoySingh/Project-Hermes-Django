from __future__ import unicode_literals

import uuid

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    user = models.ForeignKey(User)
    reputation = models.FloatField(default=0)

    def __str__(self):
        return self.user.first_name + '[' + self.user.email + ']'


class UserToken(models.Model):
    user = models.ForeignKey(User)
    token = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(default=timezone.now)
    has_expired = models.BooleanField(default=False)

    def is_active(self):
        if self.has_expired:
            return False

        current_date = timezone.now()
        diff = abs((current_date - self.last_accessed).days)

        if diff > 30:
            self.has_expired = True
            self.save()
            return False
        else:
            self.last_accessed = current_date
            self.save()
            return True
