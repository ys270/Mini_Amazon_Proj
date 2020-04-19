from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from .forms import RegistrationForm, LoginForm, SearchProductForm
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
    return render(request, 'amazon_web/index.html')

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


@login_required
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect('/amazon/')

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

@login_required
def dashboard(request,id):
    user = get_object_or_404(User,id=id)
    amazonuser = get_object_or_404(AmazonUser,user=user)
    return render(request,'amazon_web/dashboard.html',{'user':user,'amazonuser':amazonuser})


@login_required
def searchProduct(request, id):
    user = get_object_or_404(User, id=id)
    form = SearchProductForm()
    return render(request, 'amazon_web/searchProduct.html', {'form': form, 'user': user})

@login_required
def buyProduct(request,id):
    user = get_object_or_404(User, id=id)
    amazonuser = get_object_or_404(AmazonUser, user=user)
    if request.method == 'POST':
        click_search = request.POST.get("search",None)
        click_buy = request.POST.get("buy",None)
        print(click_search)
        print(click_buy)
        if click_search is not None:
            form = SearchProductForm(request.POST)
            if form.is_valid():
                part = form.cleaned_data['description']
                part = str(part)
                items = list(Product.objects.all())
                results = []
                for item in items:
                    curt = str(item.description)
                    if curt.find(part) != -1:
                        results.append(item)
                return render(request, 'amazon_web/buyProduct.html',{'results':results})
        if click_buy is not None:
            #TODO

            return HttpResponse("You have successfully make an order.")
    else:
        return HttpResponseRedirect(reverse('amazon_web:dashboard', args=[user.id]))