from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DashboardView, ReservationViewSet, RoomTypeViewSet, RoomViewSet

router = DefaultRouter()
router.register("room-types", RoomTypeViewSet)
router.register("rooms", RoomViewSet)
router.register("reservations", ReservationViewSet, basename="reservation")

urlpatterns = [path("", include(router.urls)), path("dashboard/", DashboardView.as_view(), name="dashboard")]
