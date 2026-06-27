from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('status/<str:transaction_id>/', views.payment_status, name='status'),
]
