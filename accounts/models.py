from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        RECEPTIONIST = "receptionist", "Receptionist"
        GUEST = "guest", "Guest"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role, default=Role.GUEST, db_index=True)
    phone = models.CharField(max_length=30, blank=True)
    REQUIRED_FIELDS = ["email"]
