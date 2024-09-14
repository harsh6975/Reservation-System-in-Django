from django.db import models

# Create your models here.


class Day(models.Model):
    name = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name

class Bus(models.Model):
    company_name = models.CharField(max_length=120)
    bus_number = models.CharField(max_length=20, unique=True)
    source = models.CharField(max_length=120)
    destination = models.CharField(max_length=120)
    start_time = models.TimeField()
    end_time = models.TimeField()
    frequency = models.ManyToManyField(Day) 
    capacity = models.IntegerField()

    def __str__(self):
        return f"{self.company_name} - {self.bus_number}"
    

class Reservation(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE)
    user_id = models.IntegerField()
    reservation_date = models.DateField()
    seats_reserved = models.PositiveIntegerField()

    def __str__(self):
        return f"User {self.user_id} - {self.bus.bus_number} - {self.seats_reserved} seats"