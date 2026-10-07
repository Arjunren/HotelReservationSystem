from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsHotelStaff
from .models import Reservation, Room, RoomType
from .serializers import (
    CreatePaymentSerializer, PaymentSerializer, ReservationSerializer,
    RoomSerializer, RoomTypeSerializer, TransitionSerializer,
)
from .services import transition_reservation

User = get_user_model()


class StaffWriteViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [permissions.IsAuthenticated()]
        return [IsHotelStaff()]


class RoomTypeViewSet(StaffWriteViewSet):
    queryset = RoomType.objects.all().order_by("name")
    serializer_class = RoomTypeSerializer
    search_fields = ["name", "description"]
    ordering_fields = ["name", "capacity", "nightly_rate"]


class RoomViewSet(StaffWriteViewSet):
    queryset = Room.objects.select_related("room_type").all().order_by("number")
    serializer_class = RoomSerializer
    search_fields = ["number", "room_type__name"]
    ordering_fields = ["number", "created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.query_params.get("active") in {"true", "false"}:
            queryset = queryset.filter(active=self.request.query_params["active"] == "true")
        return queryset


class ReservationViewSet(viewsets.ModelViewSet):
    serializer_class = ReservationSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]
    search_fields = ["reference", "guest__username", "room__number"]
    ordering_fields = ["check_in", "check_out", "created_at", "total_amount"]

    def get_queryset(self):
        queryset = Reservation.objects.select_related("guest", "room", "room__room_type").prefetch_related("payments__received_by")
        if self.request.user.role == User.Role.GUEST:
            queryset = queryset.filter(guest=self.request.user)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset.order_by("-created_at")

    def get_permissions(self):
        if self.action in {"transition", "payment"}:
            return [IsHotelStaff()]
        if self.action in {"update", "partial_update"}:
            return [IsHotelStaff()]
        return [permissions.IsAuthenticated()]

    @action(detail=True, methods=["patch"])
    def transition(self, request, pk=None):
        serializer = TransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reservation = transition_reservation(reservation=self.get_object(), new_status=serializer.validated_data["status"])
        return Response({"data": ReservationSerializer(reservation, context={"request": request}).data})

    @action(detail=True, methods=["post"])
    def payment(self, request, pk=None):
        serializer = CreatePaymentSerializer(data=request.data, context={"request": request, "reservation": self.get_object()})
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()
        return Response({"data": PaymentSerializer(payment).data}, status=status.HTTP_201_CREATED)


class DashboardView(APIView):
    permission_classes = [IsHotelStaff]

    def get(self, request):
        occupancy = Reservation.objects.filter(status=Reservation.Status.CHECKED_IN).count()
        booked = Reservation.objects.filter(status=Reservation.Status.BOOKED).count()
        revenue = Reservation.objects.aggregate(total=Sum("payments__amount"))["total"] or 0
        room_summary = Room.objects.values("active").annotate(total=Count("id")).order_by("active")
        return Response({"data": {"checked_in": occupancy, "booked": booked, "payments_received": revenue, "rooms": list(room_summary)}})

# Create your views here.
