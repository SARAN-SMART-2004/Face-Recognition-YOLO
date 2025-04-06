from django.urls import path
from .views import index, upload_face, start_recognition,attendance_view,unknown_faces_view

urlpatterns = [
    path('', index, name='index'),
    path('upload/', upload_face, name='upload_face'),
    path('start_recognition/', start_recognition, name='start_recognition'),
    path('attendance/', attendance_view, name='attendance'),
    path('unknown_faces/', unknown_faces_view, name='unknown_faces'),
]
