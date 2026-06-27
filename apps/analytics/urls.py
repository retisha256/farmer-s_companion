from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('summary/', views.usage_summary, name='summary'),
]
