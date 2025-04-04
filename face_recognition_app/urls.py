from django.urls import path
from .views import index, upload_face, start_recognition

urlpatterns = [
    path('', index, name='index'),
    path('upload/', upload_face, name='upload_face'),
    path('start_recognition/', start_recognition, name='start_recognition'),
]
