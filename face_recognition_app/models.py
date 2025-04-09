from django.db import models
from datetime import datetime, date, timedelta

class KnownPerson(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='known_faces/')
    email = models.EmailField(null=True,unique=True)
    encoding = models.BinaryField()
    @property
    def employee(self):
        return getattr(self, 'employeelogin', None)
    

    def __str__(self):
        return self.name
class UnknownPerson(models.Model):
    label = models.CharField(max_length=20, unique=True)
    encoding = models.BinaryField()
    image = models.ImageField(upload_to='unknown_faces/', blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.label
    
    
class Attendance(models.Model):
    name = models.CharField(max_length=100)
    timestamp = models.DateTimeField(default=datetime.now)
    date = models.DateField(default=datetime.today)
    in_time = models.TimeField(null=True, blank=True)
    out_time = models.TimeField(null=True, blank=True)
    def working_hours(self):
        if self.out_time and self.in_time:
            delta = datetime.combine(self.date, self.out_time) - datetime.combine(self.date, self.in_time)
            return round(delta.total_seconds() / 3600, 2)  # Convert to hours
        return 0


    def __str__(self):
        return f"{self.name} - {self.date}"
    
    
    
    
# face_recognition_app/models.py

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class EmployeeLogin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    known_person = models.OneToOneField('KnownPerson', on_delete=models.CASCADE)
    raw_password = models.CharField(max_length=128, null=True, blank=True)

    def __str__(self):
        return self.user.username

    def clean(self):
        if not KnownPerson.objects.filter(name=self.user.username).exists():
            raise ValidationError("Username must match a KnownPerson name.")
