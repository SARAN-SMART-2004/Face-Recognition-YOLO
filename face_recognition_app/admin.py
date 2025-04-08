from django.contrib import admin

from .models import KnownPerson, UnknownPerson, Attendance

admin.site.register(KnownPerson)
admin.site.register(UnknownPerson)
admin.site.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['name', 'date', 'in_time', 'out_time']
