from django.contrib import admin

# Register your models here.
from .models import Race, Track, Car

admin.site.register(Race)
admin.site.register(Track)
admin.site.register(Car)