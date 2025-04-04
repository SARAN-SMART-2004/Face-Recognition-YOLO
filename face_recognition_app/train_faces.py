import face_recognition
import numpy as np
import os
from django.core.files.base import ContentFile
from .models import KnownPerson

def train_faces():
    path = 'media/known_faces/'
    for filename in os.listdir(path):
        if filename.endswith(".jpg") or filename.endswith(".png"):
            file_path = os.path.join(path, filename)
            image = face_recognition.load_image_file(file_path)
            encodings = face_recognition.face_encodings(image)

            if encodings:
                encoding_array = encodings[0].tobytes()
                name = filename.split('.')[0]

                if not KnownPerson.objects.filter(name=name).exists():
                    person = KnownPerson(name=name, encoding=encoding_array)
                    person.save()
                    print(f"Saved {name} to database")
