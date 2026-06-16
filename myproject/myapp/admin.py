from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Flight, Booking

admin.site.register(Flight)
admin.site.register(Booking)
