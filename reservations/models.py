from django.conf import settings
from django.db import models


class RoomType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    capacity = models.PositiveSmallIntegerField()
    nightly_rate = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)


class Room(models.Model):
    number = models.CharField(max_length=20, unique=True)
    room_type = models.ForeignKey(RoomType, on_delete=models.PROTECT, related_name="rooms")
    active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Reservation(models.Model):
    class Status(models.TextChoices):
        BOOKED = "booked", "Booked"
        CHECKED_IN = "checked_in", "Checked in"
        CHECKED_OUT = "checked_out", "Checked out"
        CANCELLED = "cancelled", "Cancelled"

    reference = models.CharField(max_length=24, unique=True)
    guest = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reservations")
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name="reservations")
    check_in = models.DateField(db_index=True)
    check_out = models.DateField(db_index=True)
    guests = models.PositiveSmallIntegerField(default=1)
    nightly_rate = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status, default=Status.BOOKED, db_index=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_reservations")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Payment(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.PROTECT, related_name="payments")
    reference = models.CharField(max_length=80, unique=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    method = models.CharField(max_length=20, choices=[("cash", "Cash"), ("card", "Card"), ("transfer", "Transfer")])
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    paid_at = models.DateTimeField(auto_now_add=True)
