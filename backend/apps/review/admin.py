from django.contrib import admin

from .models import AnomalyFlag, ReviewItem

admin.site.register(ReviewItem)
admin.site.register(AnomalyFlag)
