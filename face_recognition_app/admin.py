from django.contrib import admin
from .models import KnownPerson, UnknownPerson, Attendance, EmployeeLogin

@admin.register(KnownPerson)
class KnownPersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'email')
    list_filter = ('name',)  # Filtering by name


@admin.register(UnknownPerson)
class UnknownPersonAdmin(admin.ModelAdmin):
    list_display = ('label', 'uploaded_at')
    list_filter = ('label', 'uploaded_at')  # Includes upload date filter


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'in_time', 'out_time', 'timestamp')
    list_filter = ('name', 'date')  # Filter by name and date


@admin.register(EmployeeLogin)
class EmployeeLoginAdmin(admin.ModelAdmin):
    list_display = ('user', 'known_person')
    list_filter = ('user', 'known_person')  # Filter by linked name
