from django.urls import path
from . import views

app_name = 'weather'

urlpatterns = [
    path('current/', views.weather_by_location, name='current'),
]
