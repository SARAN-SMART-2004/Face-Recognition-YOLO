from django.shortcuts import render, redirect
from django.http import JsonResponse
import threading
from .models import KnownPerson
from .webcam_recognition import recognize_faces_webcam
from .train_faces import train_faces

def index(request):
    return render(request, 'index.html')

def upload_face(request):
    if request.method == "POST":
        name = request.POST["name"]
        image = request.FILES["image"]
        person = KnownPerson(name=name, image=image)
        person.save()
        train_faces()  # Retrain after adding a new face
        return redirect("index")
    return render(request, "train.html")

def start_recognition(request):
    threading.Thread(target=recognize_faces_webcam).start()
    return JsonResponse({"message": "Recognition started"})
