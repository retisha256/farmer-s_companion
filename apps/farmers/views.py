from django.shortcuts import render, get_object_or_404
from .models import Farmer


def dashboard(request):
    """Farmer dashboard."""
    return render(request, 'farmers/dashboard.html')


def profile(request, pk):
    """Farmer profile detail."""
    farmer = get_object_or_404(Farmer, pk=pk)
    return render(request, 'farmers/profile.html', {'farmer': farmer})


def login_view(request):
    """Farmer login page."""
    return render(request, 'farmers/login.html')
