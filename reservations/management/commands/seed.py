from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from reservations.models import Room, RoomType

User = get_user_model()


class Command(BaseCommand):
    help = "Create idempotent development users and hotel inventory"

    def handle(self, *args, **options):
        password = "ChangeMe123!"
        for username, role, email in [
            ("admin", User.Role.ADMIN, "admin@example.com"),
            ("reception", User.Role.RECEPTIONIST, "reception@example.com"),
            ("guest", User.Role.GUEST, "guest@example.com"),
        ]:
            user, created = User.objects.get_or_create(username=username, defaults={"email": email, "role": role})
            if created:
                user.set_password(password)
                user.save(update_fields=["password"])
        room_type, _ = RoomType.objects.get_or_create(
            name="Standard", defaults={"description": "Comfortable standard room", "capacity": 2, "nightly_rate": "120.00"}
        )
        Room.objects.get_or_create(number="101", defaults={"room_type": room_type})
        self.stdout.write(self.style.SUCCESS("Seed data is ready. Development password: ChangeMe123!"))
