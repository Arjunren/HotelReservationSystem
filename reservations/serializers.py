from django.contrib.auth import get_user_model
from rest_framework import serializers

from accounts.serializers import UserSerializer
from .models import Payment, Reservation, Room, RoomType
from .services import create_reservation, record_payment

User = get_user_model()


class RoomTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomType
        fields = ["id", "name", "description", "capacity", "nightly_rate", "created_at"]
        read_only_fields = ["created_at"]

    def validate_capacity(self, value):
        if value < 1:
            raise serializers.ValidationError("Capacity must be at least one.")
        return value

    def validate_nightly_rate(self, value):
        if value <= 0:
            raise serializers.ValidationError("Nightly rate must be greater than zero.")
        return value


class RoomSerializer(serializers.ModelSerializer):
    room_type_detail = RoomTypeSerializer(source="room_type", read_only=True)

    class Meta:
        model = Room
        fields = ["id", "number", "room_type", "room_type_detail", "active", "created_at"]
        read_only_fields = ["created_at"]


class PaymentSerializer(serializers.ModelSerializer):
    received_by = UserSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = ["id", "reference", "amount", "method", "received_by", "paid_at"]
        read_only_fields = ["id", "received_by", "paid_at"]


class ReservationSerializer(serializers.ModelSerializer):
    guest_detail = UserSerializer(source="guest", read_only=True)
    room_detail = RoomSerializer(source="room", read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    guest = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role=User.Role.GUEST), required=False)

    class Meta:
        model = Reservation
        fields = ["id", "reference", "guest", "guest_detail", "room", "room_detail", "check_in", "check_out", "guests", "nightly_rate", "total_amount", "status", "notes", "payments", "created_at", "updated_at"]
        read_only_fields = ["reference", "nightly_rate", "total_amount", "status", "created_at", "updated_at"]

    def create(self, validated_data):
        request = self.context["request"]
        selected_guest = validated_data.pop("guest", None)
        guest = request.user if request.user.role == User.Role.GUEST else selected_guest
        if guest is None:
            raise serializers.ValidationError({"guest": "Staff must select a guest."})
        return create_reservation(guest=guest, created_by=request.user, **validated_data)


class TransitionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Reservation.Status.choices)


class CreatePaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["reference", "amount", "method"]
        extra_kwargs = {"reference": {"required": False}}

    def create(self, validated_data):
        return record_payment(
            reservation=self.context["reservation"], received_by=self.context["request"].user,
            **validated_data,
        )
