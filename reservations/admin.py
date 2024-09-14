from django.contrib import admin
from reservations.models import Bus, Reservation, Day

# Register your models here.
admin.site.register(Bus)
admin.site.register(Reservation)
admin.site.register(Day)
