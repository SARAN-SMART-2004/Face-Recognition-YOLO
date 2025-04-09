from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils import timezone
import calendar
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.db.models import Min, Max
from datetime import datetime, timedelta
from collections import OrderedDict
from .models import Attendance
import threading 
from django.db.models import Count
from django.utils.timezone import now
from django.contrib.auth.decorators import user_passes_test
from .models import KnownPerson
from .webcam_recognition import recognize_faces_webcam
import os
from dateutil.relativedelta import relativedelta

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

from django.http import HttpResponse
import csv
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from .models import Attendance

def export_person_attendance_csv(request, person_name):
    # Get selected month/year or default to current
    month = int(request.GET.get('month', datetime.now().month))
    year = int(request.GET.get('year', datetime.now().year))

    # Set date range for that month
    start_date = datetime(year, month, 1).date()
    end_date = (start_date + relativedelta(months=1)) - timedelta(days=1)

    # Query attendance
    attendances = Attendance.objects.filter(
        name=person_name,
        date__range=(start_date, end_date)
    ).order_by('date')

    # Prepare response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{person_name}_{month}_{year}_attendance.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'In Time', 'Out Time', 'Total Hours'])

    for a in attendances:
        if a.in_time and a.out_time:
            # Combine date + time to form datetime objects
            in_datetime = datetime.combine(a.date, a.in_time)
            out_datetime = datetime.combine(a.date, a.out_time)
            total_time = (out_datetime - in_datetime).total_seconds() / 3600
        else:
            total_time = 0

        writer.writerow([
            a.date.strftime('%Y-%m-%d'),
            a.in_time.strftime('%H:%M:%S') if a.in_time else '',
            a.out_time.strftime('%H:%M:%S') if a.out_time else '',
            round(total_time, 2)
        ])

    return response
 
@user_passes_test(lambda u: u.is_superuser)
def index(request):
    known_faces_count = KnownPerson.objects.count()
    print(known_faces_count)
    today = date.today()
    today_attendance_count = Attendance.objects.filter(date=today).exclude(name__icontains='Unknown').count()
    today_unknown_count = Attendance.objects.filter(date=today, name__icontains='Unknown').count()  
    present_names = Attendance.objects.filter(date=today).values_list('name', flat=True)
    
    absentees = KnownPerson.objects.exclude(name__in=present_names).count()
    return render(request, 'index.html', {
        'known_faces_count': known_faces_count,
        'today_attendance_count': today_attendance_count,
        'today_unknown_count':today_unknown_count,
        'absentees': absentees
    })

@user_passes_test(lambda u: u.is_superuser) 
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

@user_passes_test(lambda u: u.is_superuser)
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
@user_passes_test(lambda u: u.is_superuser)
def unknown_faces_view(request):
    unknown_faces = UnknownPerson.objects.all()
    return render(request, 'unknown_faces.html', {'unknown_faces': unknown_faces})




from .models import Attendance

def db_attendance_view(request):
    today = datetime.now().date()
    records = Attendance.objects.filter(date=today).order_by('timestamp')
    return render(request, 'db_attendance.html', {'records': records, 'date': today})



@user_passes_test(lambda u: u.is_superuser)



def analytics_view(request):
    today = timezone.now().date()
    selected_year = int(request.GET.get('year', today.year))
    selected_month = int(request.GET.get('month', today.month))

    # First and last day of the month
    first_day = datetime(selected_year, selected_month, 1).date()
    last_day = datetime(selected_year, selected_month, calendar.monthrange(selected_year, selected_month)[1]).date()

    # Get attendance counts grouped by date
    records = Attendance.objects.filter(date__range=(first_day, last_day)) \
        .values('date').annotate(count=Count('id')).order_by('date')

    # Fill missing days with 0
    date_range = [first_day + timedelta(days=i) for i in range((last_day - first_day).days + 1)]
    attendance_data = OrderedDict((day.strftime('%Y-%m-%d'), 0) for day in date_range)

    for record in records:
        date_str = record['date'].strftime('%Y-%m-%d')
        attendance_data[date_str] = record['count']

    context = {
        'date_labels': list(attendance_data.keys()),
        'attendance_counts': list(attendance_data.values()),
        'total_entries': Attendance.objects.count(),
        'unique_persons': Attendance.objects.values('name').distinct().count(),
        'total_days': Attendance.objects.values('date').distinct().count(),
        'persons': Attendance.objects.values('name').distinct(),
        'selected_month': selected_month,
        'selected_year': selected_year,
    }
    return render(request, 'analytics.html', context)

# views.py
from datetime import date, datetime, timedelta
import calendar
from collections import defaultdict
from django.shortcuts import render
from .models import Attendance
@user_passes_test(lambda u: u.is_superuser)
def person_attendance(request, person_name):
    today = date.today()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    start_date = date(year, month, 1)
    end_day = calendar.monthrange(year, month)[1]
    end_date = date(year, month, end_day)

    # Get all attendance records for person in this month
    records = Attendance.objects.filter(name=person_name, date__range=(start_date, end_date))

    # Build attendance dictionary with hours
    attendance_data = {record.date: record.working_hours() for record in records}

    # Fill missing dates with 0 hours
    for day in range(1, end_day + 1):
        d = date(year, month, day)
        if d not in attendance_data and d.weekday() != 6:  # Skip Sundays
            attendance_data[d] = 0

    # Build calendar weeks
    cal = calendar.Calendar()
    calendar_weeks = cal.monthdatescalendar(year, month)

    # Chart Data
    chart_data = [
        {"date": d.strftime("%Y-%m-%d"), "hours": attendance_data.get(d, 0)}
        for d in sorted(attendance_data)
    ]

    context = {
        "person_name": person_name,
        "attendance_data": attendance_data,
        "calendar_weeks": calendar_weeks,
        "chart_data": chart_data,
        "month": month,
        "year": year,
    }
    return render(request, "person_attendance.html", context)


# @user_passes_test(lambda u: u.is_superuser)
# def today_absentees_view(request):
#     today = date.today()
    
#     present_names = Attendance.objects.filter(date=today).values_list('name', flat=True)
    
#     absentees = KnownPerson.objects.exclude(name__in=present_names)

#     return render(request, 'today_absentees.html', {'absentees': absentees, 'today': today})

from django.contrib.auth.decorators import user_passes_test
from django.utils.timezone import localdate
from django.shortcuts import render
from django.db.models import Min, Max
from django.conf import settings
import pandas as pd
import os

from .models import Attendance, KnownPerson

@user_passes_test(lambda u: u.is_superuser)
def attendance_summary(request):
    today = localdate()

    present_names = Attendance.objects.filter(date=today).exclude(name__icontains='Unknown').values_list('name', flat=True).distinct()
    today_present_list = KnownPerson.objects.filter(name__in=present_names)
    today_unknown_names = Attendance.objects.filter(date=today, name__icontains='Unknown').values_list('name', flat=True).distinct()
    all_known_names = KnownPerson.objects.values_list('name', flat=True)
    absentees_list = KnownPerson.objects.filter(name__in=set(all_known_names) - set(present_names))

    attendance_data = (
        Attendance.objects.filter(date=today)
        .exclude(name__icontains='Unknown')
        .values('name')
        .annotate(timein=Min('timestamp'), timeout=Max('timestamp'))
        .order_by('name')
    )

    # ✅ FIXED PATH: Correct Excel location near manage.py
    excel_filename = os.path.join(settings.BASE_DIR, f"{today.strftime('%Y-%m-%d')}.xlsx")
    if os.path.exists(excel_filename):
        df = pd.read_excel(excel_filename)
        df.columns = df.columns.str.strip()
        df['Name'] = df['Name'].astype(str).str.strip()
        excel_lookup = {
            row['Name']: {
                'timein': str(row['IN Time']).split('.')[0] if pd.notna(row['IN Time']) else '',
                'timeout': str(row['OUT Time']).split('.')[0] if pd.notna(row['OUT Time']) else '',
            }
            for _, row in df.iterrows()
        }

        for rec in attendance_data:
            name = rec['name'].strip()
            if name in excel_lookup:
                rec['timein'] = excel_lookup[name]['timein']
                rec['timeout'] = excel_lookup[name]['timeout']
            else:
                rec['timein'] = rec['timein'].strftime('%H:%M:%S') if rec['timein'] else ''
                rec['timeout'] = rec['timeout'].strftime('%H:%M:%S') if rec['timeout'] else ''
    else:
        for rec in attendance_data:
            rec['timein'] = rec['timein'].strftime('%H:%M:%S') if rec['timein'] else ''
            rec['timeout'] = rec['timeout'].strftime('%H:%M:%S') if rec['timeout'] else ''

    context = {
        'today': today,
        'today_present_list': today_present_list,
        'absentees_list': absentees_list,
        'total_attendance': attendance_data,
        'today_unknown_names': today_unknown_names,
    }
    return render(request, 'attendance_summary.html', context)





from django.shortcuts import render
from datetime import datetime
from .models import Attendance  # adjust if your model name is different
from django.db.models import F
import calendar

@user_passes_test(lambda u: u.is_superuser)
def attendance_analytics(request):
    month = request.GET.get('month')
    year = request.GET.get('year')
    
    current_year = datetime.now().year
    current_month = datetime.now().month

    if not month:
        month = str(current_month)
    if not year:
        year = str(current_year)

    try:
        month = int(month)
        year = int(year)
    except ValueError:
        month = current_month
        year = current_year

    attendance_data = Attendance.objects.filter(
        date__year=year,
        date__month=month
    ).annotate(day=F('date')).order_by('date')

    day_hours = {}
    for item in attendance_data:
        day = item.date.strftime('%Y-%m-%d')
        in_time = item.in_time
        out_time = item.out_time
        if in_time and out_time:
            hours_worked = (datetime.combine(item.date, out_time) - datetime.combine(item.date, in_time)).seconds / 3600
            day_hours[day] = round(hours_worked, 2)

    chart_labels = list(day_hours.keys())
    chart_data = list(day_hours.values())

    month_choices = [(str(i), calendar.month_name[i]) for i in range(1, 13)]
    year_choices = [str(y) for y in range(current_year - 5, current_year + 1)]

    context = {
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'selected_month': str(month),
        'selected_year': str(year),
        'selected_month_name': calendar.month_name[month],
        'month_choices': month_choices,
        'year_choices': year_choices,
        'data_available': bool(chart_labels)
    }

    return render(request, 'kevin.html', context)





from django.shortcuts import render
from django.utils import timezone
from calendar import monthrange
from datetime import datetime, date
import calendar
import json
from .models import Attendance
@user_passes_test(lambda u: u.is_superuser)
def home_or_login_redirect(request):
    if request.user.is_authenticated:
        return redirect('index')
    else:
        return redirect('login')

def employees_month_performance(request):
    today = timezone.now()
    selected_month = int(request.GET.get('month', today.month))
    selected_year = int(request.GET.get('year', today.year))

    # Fetch records for selected month and year
    records = Attendance.objects.filter(date__year=selected_year, date__month=selected_month)

    # Prepare bar chart data: number of days attended (with IN and OUT times)
    attendance_count = {}
    for record in records:
        if record.in_time and record.out_time:
            in_datetime = datetime.combine(record.date, record.in_time)
            out_datetime = datetime.combine(record.date, record.out_time)
            hours = (out_datetime - in_datetime).total_seconds() / 3600

            if hours > 0:
                attendance_count[record.name] = attendance_count.get(record.name, 0) + 1

    bar_chart_data = {
        'labels': list(attendance_count.keys()),
        'data': list(attendance_count.values())
    }


    context = {
    'bar_chart_data': json.dumps(bar_chart_data),
    
    'selected_month': selected_month,
    'selected_year': selected_year,
    'year_range': list(range(2023, today.year + 1)),
    'months': list(range(1, 13)),
    'has_data': records.exists(),  # ← Add this
        }

    return render(request, 'emp_month_per.html', context)





from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

def signup_view(request):
    if request.method == 'GET':
        return render(request, 'signup.html')
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            fullname = data.get('fullname')
            email = data.get('email')
            password = data.get('password')
            terms = data.get('terms')

            if not all([fullname, email, password, terms]):
                return JsonResponse({'message': 'All fields are required including terms.'}, status=400)

            if User.objects.filter(username=email).exists():
                return JsonResponse({'message': 'User with this email already exists.'}, status=400)

            user = User.objects.create_user(username=email, email=email, password=password, first_name=fullname)
            user.save()
            return JsonResponse({'message': 'Account created successfully.', 'redirect': '/login/'})
        except Exception as e:
            return JsonResponse({'message': f'Error: {str(e)}'}, status=500)

def login_view(request):
    if request.method == 'GET':
        return render(request, 'login.html')

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')

            user = authenticate(request, username=email, password=password)
            if user is not None:
                auth_login(request, user)

                # Redirect based on role
                if user.is_superuser or user.is_staff:
                    redirect_url = '/dashboard/'
                elif EmployeeLogin.objects.filter(user=user).exists():
                    redirect_url = '/employee/attendance/'
                else:
                    return JsonResponse({'message': 'Access denied. You are not recognized as an employee.'}, status=403)

                return JsonResponse({'message': 'Login successful.', 'redirect': redirect_url})
            else:
                return JsonResponse({'message': 'Invalid email or password.'}, status=401)
        except Exception as e:
            return JsonResponse({'message': f'Error: {str(e)}'}, status=500)


def logout_view(request):
    auth_logout(request)
    return redirect('/login/')






# face_recognition_app/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from .models import EmployeeLogin, KnownPerson

def is_superadmin(user):
    return user.is_superuser

@user_passes_test(is_superadmin)
def employee_list(request):
    # All employee login entries
    employees = EmployeeLogin.objects.select_related('user', 'known_person')

    # All known persons
    known_persons = KnownPerson.objects.all()

    context = {
        'employees': employees,
        'known_persons': known_persons,  # So we can find those without login
    }
    return render(request, 'emp/employee_list.html', context)
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from .models import EmployeeLogin, KnownPerson



from django.core.mail import send_mail
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from .models import EmployeeLogin, KnownPerson

@user_passes_test(is_superadmin)
def add_employee(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not KnownPerson.objects.filter(name=username).exists():
            messages.error(request, "Username must match a KnownPerson name.")
            return redirect('add_employee')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('add_employee')

        known_person = KnownPerson.objects.get(name=username)

        # Extra safety
        if EmployeeLogin.objects.filter(known_person=known_person).exists():
            messages.error(request, "Known person already has an employee account.")
            return redirect('add_employee')

        # Create user and employee login
        user = User.objects.create_user(username=username, password=password)
        emp_login = EmployeeLogin.objects.create(
            user=user,
            known_person=known_person,
            raw_password=password
        )

        # Send email to the known person's email
        if known_person.email:
            try:
                send_mail(
                    subject="Your Employee Account Credentials",
                    message=f"Dear {username},\n\nYour employee login has been created.\n\nUsername: {username}\nPassword: {password}\n\nPlease log in and update your password after first use.",
                    from_email=None,  # uses DEFAULT_FROM_EMAIL
                    recipient_list=[known_person.email],
                    fail_silently=False,
                )
            except Exception as e:
                messages.warning(request, f"Employee created, but email failed: {str(e)}")
            else:
                messages.success(request, "Employee created and email sent successfully.")
        else:
            messages.warning(request, "Employee created, but no email was set for this KnownPerson.")

        return redirect('employee_list')

    return render(request, 'emp/add_employee.html')


from django.contrib.auth.decorators import login_required

@login_required
def employee_attendance_view(request):
    try:
        employee = EmployeeLogin.objects.get(user=request.user)
        attendance_records = Attendance.objects.filter(name=employee.known_person.name)
        return render(request, 'employee_attendance.html', {'records': attendance_records})
    except EmployeeLogin.DoesNotExist:
        return HttpResponse("Access Denied.")


from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from datetime import datetime
from .models import Attendance, EmployeeLogin

@login_required
def employee_attendance_history(request):
    user = request.user
    try:
        emp_login = EmployeeLogin.objects.get(user=user)
    except EmployeeLogin.DoesNotExist:
        return render(request, 'error.html', {'message': 'You are not registered as an employee.'})

    # Get filter values
    month = request.GET.get('month')
    year = request.GET.get('year')

    # Default to current month/year
    if not month or not year:
        today = datetime.now()
        month = today.month
        year = today.year

    # Filter attendance
    attendance_records = Attendance.objects.filter(
        name=emp_login.known_person.name,
        date__month=month,
        date__year=year
    ).order_by('date')

    context = {
        'attendance_records': attendance_records,
        'selected_month': int(month),
        'selected_year': int(year),
    }
    return render(request, 'emp/employee_attendance_history.html', context)


@user_passes_test(is_superadmin)
def edit_employee(request, emp_id):
    employee = get_object_or_404(EmployeeLogin, id=emp_id)

    if request.method == 'POST':
        username = request.POST.get('username')
        raw_password = request.POST.get('password')
        email = request.POST.get('email')
        name = request.POST.get('name')
        image = request.FILES.get('image')

        # Update user model
        employee.user.username = username
        if raw_password:
            employee.user.set_password(raw_password)
            employee.raw_password = raw_password
        employee.user.save()

        # Update known person
        person = employee.known_person
        person.name = name
        person.email = email
        if image:
            person.image = image
        person.save()

        employee.save()
        return redirect('employee_list')

    context = {
        'employee': employee,
    }
    return render(request, 'emp/edit_employee.html', context)



from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import EmployeeLogin

@login_required
def employee_profile(request):
    user = request.user
    try:
        emp = EmployeeLogin.objects.select_related('known_person').get(user=user)
    except EmployeeLogin.DoesNotExist:
        return render(request, 'error.html', {'message': 'Employee profile not found.'})

    context = {
        'employee': emp,
    }
    return render(request, 'emp/employee_profile.html', context)
