from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class Flight(models.Model):
    flight_number = models.CharField(max_length=10)
    source = models.CharField(max_length=50)
    destination = models.CharField(max_length=50)
    price = models.IntegerField()
    total_seats = models.IntegerField(default=5)
    flight_name = models.CharField(max_length=50, default="None")

    def __str__(self):
        return f"{self.flight_number}, {self.flight_name}"


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE)
    travel_date = models.DateField()
    booking_date = models.DateTimeField(auto_now_add=True)
    seat_number = models.CharField( max_length=10,default='A1')
    payment_methods = models.CharField(max_length=50,default='Unknown')

    def __str__(self):
        return f"{self.user.username}, {self.flight.flight_number}, {self.flight.flight_name}"