from django.urls import path
from .views import *

urlpatterns = [
    path('dashboard/', index, name='index'),  # Use /dashboard/ for actual homepage after login
    path('', index, name='index'),
    path('upload/', upload_face, name='upload_face'),
    path('start_recognition/', start_recognition, name='start_recognition'),
    path('attendance/', attendance_view, name='attendance'),
    path('unknown_faces/', unknown_faces_view, name='unknown_faces'),
    path('analytics/', analytics_view, name='analytics'),
    path('analytics/person/<str:person_name>/', person_attendance, name='person_attendance'),
    # path('absentees/', today_absentees_view, name='absentees'),
    path('attendance-summary/', attendance_summary, name='attendance_summary'),
    path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('company_workings/', attendance_analytics, name='kevin'),
    path('employees_month_performance/', employees_month_performance, name='employees_month_performance'),
    path('analytics/person/<str:person_name>/export/', export_person_attendance_csv, name='export_person_attendance'),
    
    
    
    
    path('employees/',employee_list, name='employee_list'),
    path('employees/add/',add_employee, name='add_employee'),
    path('employee/attendance/',employee_attendance_history, name='employee_attendance'),
    path('employee/edit/<int:emp_id>/', edit_employee, name='edit_employee'),
    path('employee/attendance-history/', employee_attendance_history, name='employee_attendance_history'),
    path('employee/profile/',employee_profile, name='employee_profile'),



]

