from django.urls import path
from . import views

app_name = 'voice'

urlpatterns = [
    path('callback/', views.voice_callback, name='callback'),
]
