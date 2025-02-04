from django.urls import path, include
from . import views

from django.contrib.auth.views import LoginView, LogoutView
app_name = 'chat'

urlpatterns = [
    path('chat/<int:appointment_id>/', views.chatPage, name='chat_room'),
    path('chat/<int:appointment_id>/end/', views.end_chat, name='end_chat'),
    path('history/', views.chat_history, name='chat_history'),
    path('submit-review/', views.submit_review, name='submit_review'),
    path('chat_ai/', views.chat_view, name='chat_view'),


]