from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('video_call/', views.video_call, name='video_call'),
]
