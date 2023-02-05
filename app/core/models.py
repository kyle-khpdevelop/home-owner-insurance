"""
Database models
"""
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models as m
from quote.constants import DataClassField
from quote.constants import QuoteFlatCostCoverages
from quote.constants import QuotePercentageCostCoverages
from quote.constants import States
from quote.utils import EnhancedJSONEncoder


class UserManager(BaseUserManager):
    """Manager for users"""

    def create_user(self, email: str, password: str | None = None, **extra_fields):
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


class Quote(m.Model):
    """Quote object"""

    user = m.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=m.CASCADE,
    )
    buyer_first_name = m.CharField(max_length=255)
    buyer_last_name = m.CharField(max_length=255)
    state = m.CharField(max_length=2, choices=States.choices)
    flat_cost_coverages = DataClassField(
        dataClass=QuoteFlatCostCoverages, encoder=EnhancedJSONEncoder
    )
    percentage_cost_coverages = DataClassField(
        dataClass=QuotePercentageCostCoverages, encoder=EnhancedJSONEncoder
    )
    monthly_subtotal = m.DecimalField(max_digits=6, decimal_places=2, default=0)
    monthly_taxes = m.DecimalField(max_digits=6, decimal_places=2, default=0)
    monthly_total = m.DecimalField(max_digits=7, decimal_places=2, default=0)
