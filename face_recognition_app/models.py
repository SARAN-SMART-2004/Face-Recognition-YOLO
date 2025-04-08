from django.db import models
from datetime import datetime, date, timedelta

class KnownPerson(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='known_faces/')
    email = models.EmailField(null=True,unique=True)
    encoding = models.BinaryField()
    

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


    def __str__(self):
        return f"{self.name} - {self.date}"