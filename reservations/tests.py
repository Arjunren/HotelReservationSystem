from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import Reservation, Room, RoomType

User = get_user_model()


@pytest.fixture
def users(db):
    return {
        "staff": User.objects.create_user("staff", "staff@example.com", "StrongPassword123!", role=User.Role.RECEPTIONIST),
        "guest": User.objects.create_user("guest", "guest@example.com", "StrongPassword123!", role=User.Role.GUEST),
        "other": User.objects.create_user("other", "other@example.com", "StrongPassword123!", role=User.Role.GUEST),
    }


@pytest.fixture
def room(db):
    category = RoomType.objects.create(name="Suite", capacity=2, nightly_rate=Decimal("150.00"))
    return Room.objects.create(number="201", room_type=category)


def client_for(user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {Token.objects.create(user=user).key}")
    return client


def booking_payload(room, **updates):
    payload = {"room": room.id, "check_in": date.today() + timedelta(days=5), "check_out": date.today() + timedelta(days=8), "guests": 2, "notes": "Late arrival"}
    payload.update(updates)
    return payload


@pytest.mark.django_db
def test_registration_always_creates_guest():
    response = APIClient().post("/api/auth/register/", {"username": "newguest", "email": "new@example.com", "password": "VeryStrongPassword123!", "role": "admin"}, format="json")
    assert response.status_code == 201
    assert response.data["data"]["user"]["role"] == User.Role.GUEST


@pytest.mark.django_db
def test_server_controls_guest_and_pricing(users, room):
    response = client_for(users["guest"]).post("/api/reservations/", booking_payload(room, guest=users["other"].id, total_amount="1.00"), format="json")
    assert response.status_code == 201
    reservation = Reservation.objects.get()
    assert reservation.guest == users["guest"]
    assert reservation.nightly_rate == Decimal("150.00")
    assert reservation.total_amount == Decimal("450.00")


@pytest.mark.django_db
def test_overlapping_booking_is_rejected(users, room):
    staff = client_for(users["staff"])
    first = staff.post("/api/reservations/", booking_payload(room, guest=users["guest"].id), format="json")
    second = staff.post("/api/reservations/", booking_payload(room, guest=users["other"].id), format="json")
    assert first.status_code == 201
    assert second.status_code == 400
    assert Reservation.objects.count() == 1


@pytest.mark.django_db
def test_guest_cannot_see_another_guests_reservation(users, room):
    reservation = Reservation.objects.create(
        reference="HTL-PRIVATE", guest=users["other"], room=room, check_in=date.today() + timedelta(days=2),
        check_out=date.today() + timedelta(days=3), nightly_rate="150", total_amount="150", created_by=users["staff"],
    )
    response = client_for(users["guest"]).get(f"/api/reservations/{reservation.id}/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_staff_can_record_payment_but_not_overpay(users, room):
    reservation = Reservation.objects.create(
        reference="HTL-PAID", guest=users["guest"], room=room, check_in=date.today() + timedelta(days=2),
        check_out=date.today() + timedelta(days=4), nightly_rate="150", total_amount="300", created_by=users["staff"],
    )
    client = client_for(users["staff"])
    paid = client.post(f"/api/reservations/{reservation.id}/payment/", {"amount": "200.00", "method": "card"}, format="json")
    overpaid = client.post(f"/api/reservations/{reservation.id}/payment/", {"amount": "101.00", "method": "cash"}, format="json")
    assert paid.status_code == 201
    assert overpaid.status_code == 400
    assert reservation.payments.count() == 1
