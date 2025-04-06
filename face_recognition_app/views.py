from django.shortcuts import render, redirect
from django.http import JsonResponse
import threading 
from .models import KnownPerson
from .webcam_recognition import recognize_faces_webcam
from .train_faces import train_faces
import os
import pandas as pd
from datetime import datetime
from .models import UnknownPerson


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
from .cam_face_logger import start_all_cameras

# def start_cctv_recognition(request):
#     Thread(target=start_all_cameras).start()
#     return JsonResponse({"message": "CCTV face recognition started"})
# def attendance_view(request):
#     # Get today's date
#     today = datetime.now().strftime('%Y-%m-%d')
#     excel_file = f'{today}.xlsx'

#     # Check if file exists
#     if os.path.exists(excel_file):
#         df = pd.read_excel(excel_file)
#         data = df.to_dict(orient='records')
#     else:
#         data = []

#     return render(request, 'attendance.html', {'data': data, 'date': today})

import os
import pandas as pd
from django.shortcuts import render
from datetime import datetime, timedelta


def attendance_view(request):
    day = request.GET.get('day')
    month = request.GET.get('month')
    year = request.GET.get('year')

    # Set default to today if not selected
    if day and month and year:
        selected_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    else:
        selected_date = datetime.now().strftime('%Y-%m-%d')
        day = selected_date[8:10]
        month = selected_date[5:7]
        year = selected_date[0:4]

    excel_file = f'{selected_date}.xlsx'

    if os.path.exists(excel_file):
        df = pd.read_excel(excel_file)
        data = df.to_dict(orient='records')
    else:
        data = []

    return render(request, 'attendance.html', {
        'data': data,
        'selected_date': selected_date,
        'day': day,
        'month': month,
        'year': year,
    })



# face_recognition_app/views.py
from django.shortcuts import render
from .models import UnknownPerson

def unknown_faces_view(request):
    unknown_faces = UnknownPerson.objects.all()
    return render(request, 'unknown_faces.html', {'unknown_faces': unknown_faces})
