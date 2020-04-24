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
def rate(request,id):
    user = get_object_or_404(User, id=id)
    amazonuser = get_object_or_404(AmazonUser, user=user)
    if request.method == 'POST':
        pkgid = request.POST.get("pkgid",None)
        score = request.POST.get("score",None)
        if pkgid and score:
            order = Order.objects.get(pkgid=pkgid)
            if not order.rate_score:
                order.rate_score = int(score)
                order.save()
            item = Product.objects.get(item_id=order.item_id)
            item.rate_count += 1
            item.total_score += int(score)
            item.avg_score = item.total_score/item.rate_count
            item.save()
        return HttpResponseRedirect(reverse('amazon_web:dashboard', args=[user.id]))
    else:
        orders = Order.objects.filter(status='delivered',userid=user.id,rate_score__isnull=True)
        return render(request,'amazon_web/rate.html',{'orders':orders,'user':user})

@login_required
def searchProduct(request, id):
    user = get_object_or_404(User, id=id)
    form = SearchProductForm()
    products = Product.objects.all()
    return render(request, 'amazon_web/searchProduct.html', {'form': form, 'user': user,'products':products})

@login_required
def buyProduct(request,id):
    user = get_object_or_404(User, id=id)
    amazonuser = get_object_or_404(AmazonUser, user=user)
    if request.method == 'POST':
        click_search = request.POST.get("search",None)
        click_buy = request.POST.get("buy",None)
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
                return render(request, 'amazon_web/buyProduct.html',{'results':results,'user': user})
        if click_buy is not None:
            #TODO
            #get data from the form
            item_name = request.POST.get("item_name")
            purchase_num = int(request.POST.get("purchase_num"))
            x = request.POST.get("x")
            y = request.POST.get("y")
            upsid = request.POST.get("upsid")
            product_list = Product.objects.all()
            find = False
            for product in product_list:
                if product.name == item_name:
                    find = True
                    # add new order, is_enough field is always false even when the warehouse has enough products currently
                    # because we buy exactly the num clients need every time, 有时候可能因为消息到来的先后顺序，导致目前库存还有富余
                    # 但事实是，每来一个新订单，我们都需要purchase more
                    neworder = Order(userid=id, ups_username=upsid, x=x, y=y, item_name=item_name, item_id=product.item_id,
                                     purchase_num=purchase_num, is_enough=False, status = 'packing')
                    neworder.save()
            #new product type need to be added
            if find == False:
                #add new product
                newproduct = Product(name=item_name, description=item_name)
                newproduct.save()
                #add new order
                neworder = Order(userid=id, ups_username=upsid, x=x, y=y, item_name=item_name, item_id=newproduct.item_id,
                                 purchase_num=purchase_num, is_enough=False, status = 'packing')
                neworder.save()
            return render(request,'amazon_web/successful_buy.html',{'user': user})
    else:
        return HttpResponseRedirect(reverse('amazon_web:dashboard', args=[user.id]))

@login_required
def query(request, id):
    user = get_object_or_404(User, id=id)
    amazonuser = get_object_or_404(AmazonUser, user=user)
    packages = Order.objects.filter(userid=id)
    packages = list(packages)
    return render(request,'amazon_web/query.html',{'pck_list':packages,'user': user})

@login_required
def query_one(request, id):
    user = get_object_or_404(User, id=id)
    amazonuser = get_object_or_404(AmazonUser, user=user)
    if request.method == 'POST':
        pkgid = request.POST.get("pkgid")
        print(pkgid)
        order = Order.objects.filter(pkgid=pkgid)
        order = order[0]
        return render(request,'amazon_web/query_one.html',{'order':order, 'user': user})
    else:
        return HttpResponseRedirect(reverse('amazon_web:dashboard', args=[user.id]))

@login_required
def edit_profile(request, id):
    user = get_object_or_404(User, id=id)
    amazonuser = get_object_or_404(AmazonUser, user=user)
    if request.method == 'POST':
        email = request.POST.get("user_email")
        user.email = email
        user.save()
        amazonuser.user = user
        amazonuser.save()
        return HttpResponseRedirect(reverse('amazon_web:dashboard', args=[user.id]))
    return render(request,'amazon_web/edit_profile.html',{'user': user})