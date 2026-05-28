from django.contrib import admin

from .models import Membership, Organization, User

admin.site.register(Organization)
admin.site.register(Membership)
admin.site.register(User)
