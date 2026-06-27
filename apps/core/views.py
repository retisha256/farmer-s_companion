from django.shortcuts import render


def index(request):
    """Home page view."""
    return render(request, 'core/index.html')
