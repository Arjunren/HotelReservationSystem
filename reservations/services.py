import secrets
from datetime import date
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from rest_framework.exceptions import ValidationError

from .models import Payment, Reservation, Room


def _reference(prefix):
    return f"{prefix}-{secrets.token_hex(5).upper()}"


@transaction.atomic
def create_reservation(*, guest, room, check_in, check_out, guests, notes, created_by):
    room = Room.objects.select_for_update().select_related("room_type").get(pk=room.pk)
    if not room.active:
        raise ValidationError({"room": "This room is unavailable."})
    if check_out <= check_in:
        raise ValidationError({"check_out": "Check-out must be after check-in."})
    if check_in < date.today():
        raise ValidationError({"check_in": "Check-in cannot be in the past."})
    if guests < 1 or guests > room.room_type.capacity:
        raise ValidationError({"guests": f"Guest count must be between 1 and {room.room_type.capacity}."})
    conflict = Reservation.objects.filter(
        room=room,
        status__in=[Reservation.Status.BOOKED, Reservation.Status.CHECKED_IN],
        check_in__lt=check_out,
        check_out__gt=check_in,
    ).exists()
    if conflict:
        raise ValidationError({"room": "Room is already reserved for these dates."})
    nightly_rate = room.room_type.nightly_rate
    total_amount = Decimal((check_out - check_in).days) * nightly_rate
    return Reservation.objects.create(
        reference=_reference("HTL"), guest=guest, room=room, check_in=check_in,
        check_out=check_out, guests=guests, nightly_rate=nightly_rate,
        total_amount=total_amount, notes=notes, created_by=created_by,
    )


@transaction.atomic
def transition_reservation(*, reservation, new_status):
    reservation = Reservation.objects.select_for_update().get(pk=reservation.pk)
    transitions = {
        Reservation.Status.BOOKED: {Reservation.Status.CHECKED_IN, Reservation.Status.CANCELLED},
        Reservation.Status.CHECKED_IN: {Reservation.Status.CHECKED_OUT},
        Reservation.Status.CHECKED_OUT: set(),
        Reservation.Status.CANCELLED: set(),
    }
    if new_status not in transitions[reservation.status]:
        raise ValidationError({"status": f"Cannot change {reservation.status} to {new_status}."})
    if new_status == Reservation.Status.CHECKED_IN and not (reservation.check_in <= date.today() < reservation.check_out):
        raise ValidationError({"status": "Check-in is only allowed during the reserved stay."})
    reservation.status = new_status
    reservation.save(update_fields=["status", "updated_at"])
    return reservation


@transaction.atomic
def record_payment(*, reservation, amount, method, received_by, reference=""):
    reservation = Reservation.objects.select_for_update().get(pk=reservation.pk)
    if reservation.status == Reservation.Status.CANCELLED:
        raise ValidationError({"reservation": "Cancelled reservations cannot receive payments."})
    paid = reservation.payments.aggregate(total=Sum("amount"))["total"] or Decimal("0")
    if amount <= 0:
        raise ValidationError({"amount": "Payment must be greater than zero."})
    if paid + amount > reservation.total_amount:
        raise ValidationError({"amount": "Payment would exceed the reservation balance."})
    return Payment.objects.create(
        reservation=reservation, reference=reference or _reference("PAY"), amount=amount,
        method=method, received_by=received_by,
    )
