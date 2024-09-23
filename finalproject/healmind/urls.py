# In your `urls.py`
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from healmind.views import *
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [

    path('', home_view, name='home'),
    # authentication
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', register_view, name='register'),



]