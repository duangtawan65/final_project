from django.urls import path, include
from . import views

from django.contrib.auth.views import LoginView, LogoutView
app_name = 'chat'

urlpatterns = [
    path('rooms/', views.chatPage, name='chat_rooms'),

]