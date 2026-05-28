from django.contrib import admin

from .models import IngestionBatch, RawRecord, SourceConnection

admin.site.register(SourceConnection)
admin.site.register(IngestionBatch)
admin.site.register(RawRecord)
