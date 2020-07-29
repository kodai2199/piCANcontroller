from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from .models import Installation
from django.views import generic


@login_required
def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')

    # Loads the list of installations
    installations = Installation.objects.all()

    context = {
        'installations': installations,
        'installations_count': installations.count(),
    }

    # TODO: check if the installation is online or offline!!!
    return render(request, 'dashboard.html', context=context)


