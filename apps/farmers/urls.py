from django.urls import path
from . import views

app_name = 'farmers'

urlpatterns = [
    path('register/', views.RegisterFarmerView.as_view(), name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/<int:pk>/', views.profile, name='profile'),
    path('login/', views.login_view, name='login'),
]
