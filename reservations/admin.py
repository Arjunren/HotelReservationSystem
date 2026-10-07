from django.contrib import admin

from .models import Payment, Reservation, Room, RoomType

admin.site.register([RoomType, Room, Reservation, Payment])

# Register your models here.
