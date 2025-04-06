from django.db import models

class KnownPerson(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='known_faces/')
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