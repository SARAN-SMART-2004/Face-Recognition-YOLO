from django.shortcuts import render, redirect
from django.http import JsonResponse
import threading 
from .models import KnownPerson
from .webcam_recognition import recognize_faces_webcam
import os
from django.db.models.functions import TruncDate
from django.db.models import Count
import pandas as pd
from datetime import timedelta, date
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from .models import Attendance
import json
from datetime import datetime
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from .models import UnknownPerson,KnownPerson
import face_recognition

 
def index(request):
    
    return render(request, 'index.html')

 
def upload_face(request):
    if request.method == "POST":
        name = request.POST["name"]
        email = request.POST["email"]
        image_file = request.FILES["image"]

        if KnownPerson.objects.filter(name=name).exists():
            print(f"⚠ Name '{name}' already exists.")
        else:
            # Save the uploaded image temporarily
            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'known_faces'))
            filename = fs.save(image_file.name, image_file)
            image_path = os.path.join(settings.MEDIA_ROOT, 'known_faces', filename)

            # Load and encode face
            image = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image)

            if encodings:
                encoding_array = encodings[0].tobytes()
                person = KnownPerson(name=name, email=email, encoding=encoding_array)
                with open(image_path, 'rb') as f:
                    person.image.save(filename, f, save=False)
                person.save()
                print(f"✔ Trained and saved: {name}")
            else:
                print(f"❌ No face found in image: {filename}")
                os.remove(image_path)

        return redirect("index")
    return render(request, "train.html")
 
def start_recognition(request):
    threading.Thread(target=recognize_faces_webcam).start()
    return JsonResponse({"message": "Recognition started"})
# from .cam_face_logger import start_all_cameras

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




from .models import Attendance

def db_attendance_view(request):
    today = datetime.now().date()
    records = Attendance.objects.filter(date=today).order_by('timestamp')
    return render(request, 'db_attendance.html', {'records': records, 'date': today})



 
def analytics_view(request):
    from .models import Attendance
    from django.db.models import Count
    from django.utils import timezone
    import json
    from datetime import timedelta

    today = timezone.now().date()
    one_month_ago = today - timedelta(days=30)

    # Date-wise attendance counts
    daily_data = Attendance.objects.filter(timestamp__date__gte=one_month_ago)\
        .extra(select={'date': "DATE(timestamp)"})\
        .values('date').annotate(count=Count('id')).order_by('date')

    date_labels = [str(entry['date']) for entry in daily_data]
    attendance_counts = [entry['count'] for entry in daily_data]

    # Stats
    total_entries = Attendance.objects.count()
    unique_persons = Attendance.objects.values('name').distinct().count()
    total_days = Attendance.objects.dates('timestamp', 'day').count()
    persons = Attendance.objects.values('name').distinct()

    return render(request, 'analytics.html', {
        'date_labels': json.dumps(date_labels),
        'attendance_counts': json.dumps(attendance_counts),
        'total_entries': total_entries,
        'unique_persons': unique_persons,
        'total_days': total_days,
        'persons': persons
    })



 
def person_attendance(request, name):
    records = Attendance.objects.filter(name=name).order_by('date')

    attendance = []
    daily_counts = {}
    daily_hours = {}

    for record in records:
        total_hours = None
        if record.in_time and record.out_time:
            in_dt = datetime.combine(record.date, record.in_time)
            out_dt = datetime.combine(record.date, record.out_time)
            total_hours = round((out_dt - in_dt).total_seconds() / 3600, 2)

        attendance.append({
            'date': record.date,
            'in_time': record.in_time,
            'out_time': record.out_time,
            'hours': total_hours
        })

        date_str = str(record.date)
        daily_counts[date_str] = daily_counts.get(date_str, 0) + 1
        daily_hours[date_str] = daily_hours.get(date_str, 0) + (total_hours if total_hours else 0)

    context = {
        'name': name,
        'attendance': attendance,
        'date_labels': list(daily_counts.keys()),
        'date_counts': list(daily_hours.values()),  # Updated to show hours
    }
    return render(request, 'person_attendance.html', context)


@csrf_exempt  # only for development; for production use @csrf_protect with token
def signup_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            fullname = data.get('fullname')
            email = data.get('email')
            password = data.get('password')
            terms = data.get('terms')

            if not all([fullname, email, password, terms]):
                return JsonResponse({'message': 'All fields are required.'}, status=400)

            if User.objects.filter(username=email).exists():
                return JsonResponse({'message': 'User already exists.'}, status=400)

            # Create user
            user = User.objects.create_user(username=email, email=email, password=password)
            user.first_name = fullname
            user.save()

            return JsonResponse({
                'message': 'Account created successfully!',
                'redirect': '/login/'  # or wherever you want to redirect
            }, status=200)

        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)

    return JsonResponse({'message': 'Invalid request method'}, status=405)

def login_page(request):
    return render(request, 'login.html')

@csrf_exempt
def login_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode('utf-8'))
            username = data.get('username')
            password = data.get('password')

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return JsonResponse({'status': 'success', 'redirect': '/dashboard/'})
            else:
                return JsonResponse({'status': 'fail', 'message': 'Invalid credentials'}, status=401)
        except Exception as e:
            return JsonResponse({'status': 'fail', 'message': str(e)}, status=400)
    else:
        return JsonResponse({'message': 'Only POST allowed'}, status=405)
# Logout view

def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('login')


    