from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from .forms import RegistrationForm, LoginForm
from .models import AmazonUser, Warehouse, Product, Order
from django.urls import reverse
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse,HttpResponseRedirect
import socket
# Create your views here.

# Welcome page
def index(request):
    return render(request, 'amazon_web/index.html',{})

# Login page
def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = auth.authenticate(username=username, password=password)
            if user is not None and user.is_active:
                auth.login(request, user)
                # TODO: dashboard
                return HttpResponseRedirect(reverse('amazon_web:dashboard', args=[user.id]))
            else:
                return render(request, 'amazon_web/login.html',
                              {'form': form, 'message': 'Wrong password. Please try again.'})
    else:
        form = LoginForm()

    return render(request, 'amazon_web/login.html', {'form': form})

# User register
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password2']
            user = User.objects.create_user(username=username,
                                            password=password,
                                            email=email)

            user_profile = AmazonUser(user=user)
            user_profile.save()
            return HttpResponseRedirect(reverse('amazon_web:login'))

    else:
        form = RegistrationForm()
    return render(request, 'amazon_web/register.html', {'form': form})

# TODO dashboard
def dashboard(request,id):
    s = "dashboard"
    s += str(id)
    return HttpResponse(s)