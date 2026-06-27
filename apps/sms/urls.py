from django.urls import path
from . import views

app_name = 'sms'

urlpatterns = [
    path('callback/', views.sms_callback, name='callback'),
]
