from django.contrib import admin

from .models import AirportCode, EmissionFactor, PlantCode

admin.site.register(EmissionFactor)
admin.site.register(PlantCode)
admin.site.register(AirportCode)
