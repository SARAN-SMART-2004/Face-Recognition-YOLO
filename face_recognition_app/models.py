from django.db import models

class KnownPerson(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='known_faces/')
    encoding = models.BinaryField()

    def __str__(self):
        return self.name
