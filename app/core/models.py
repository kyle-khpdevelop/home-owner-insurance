"""
Database models
"""
import json
from dataclasses import dataclass

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models as m
from django.utils.translation import gettext_lazy as _
from quote.utils import EnhancedJSONEncoder

# Used to create dataclasses from dictionary


class DataClassField(m.JSONField):
    """Map Python's dataclass to model."""

    def __init__(self, dataClass, *args, **kwargs):
        self.dataClass = dataClass
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["dataClass"] = self.dataClass
        return name, path, args, kwargs

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        obj = json.loads(value)
        return obj

    def to_python(self, value):
        if isinstance(value, self.dataClass):
            return value
        if value is None:
            return value
        obj = json.loads(value)
        return obj

    def get_prep_value(self, value):
        if value is None:
            return value
        return json.dumps(value)


class UserManager(BaseUserManager):
    """Manager for users"""

    def create_user(self, email, password=None, **extra_fields):
        """Create, save and return a new user"""
        if not email:
            raise ValueError("User must have an email address")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password, **extra_fields):
        """Create and return a new superuser"""
        if not email:
            raise ValueError("Superuser must have an email address")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """User in the system"""

    email = m.EmailField(max_length=255, unique=True)
    name = m.CharField(max_length=255)
    is_active = m.BooleanField(default=True)
    is_staff = m.BooleanField(default=False)

    # Assigns a Custom UserManager to a User
    objects = UserManager()

    USERNAME_FIELD = "email"


class QuoteCoverageTypes(m.TextChoices):
    Basic = "Basic", _("Basic")
    Premium = "Premium", _("Premium")


class States(m.TextChoices):
    California = "CA", _("California")
    Texas = "TX", _("Texas")
    New_York = "NY", _("New York")


@dataclass
class QuoteAdditionalCoverages:
    flood_coverage: bool

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)


class Quote(m.Model):
    """Quote object"""

    user = m.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=m.CASCADE,
    )
    buyer_first_name = m.CharField(max_length=255)
    buyer_last_name = m.CharField(max_length=255)
    coverage_type = m.CharField(max_length=100, choices=QuoteCoverageTypes.choices)
    pet_coverage = m.BooleanField(default=False)
    state = m.CharField(max_length=2, choices=States.choices)
    additional_coverage = DataClassField(
        dataClass=QuoteAdditionalCoverages, encoder=EnhancedJSONEncoder
    )
