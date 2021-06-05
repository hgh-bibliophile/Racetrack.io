from django.contrib import admin

# Register your models here.
from .models import Race, Track, Car, Run, Trial

admin.site.register(Race)
admin.site.register(Track)
admin.site.register(Run)
admin.site.register(Car)
admin.site.register(Trial)