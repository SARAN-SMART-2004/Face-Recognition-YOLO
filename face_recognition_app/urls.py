from django.urls import path
from .views import *

urlpatterns = [
    path('', index, name='index'),  # This is your home/index page
    path('upload/', upload_face, name='upload_face'),
    path('start_recognition/', start_recognition, name='start_recognition'),
    path('attendance/', attendance_view, name='attendance'),
    path('unknown_faces/', unknown_faces_view, name='unknown_faces'),
    path('analytics/', analytics_view, name='analytics'),
    path('analytics/person/<str:name>/', person_attendance, name='person_attendance'),

    # ✅ Correct login, signup, logout URLs
    path('login/', login_view, name='login'),
    path('',login_page, name='login_page'),
    path('signup/', signup_view, name='signup'),
    path('logout/', logout_view, name='logout'),
]
