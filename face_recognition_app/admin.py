from django.contrib import admin
from .models import KnownPerson, UnknownPerson

admin.site.register(KnownPerson)
admin.site.register(UnknownPerson)