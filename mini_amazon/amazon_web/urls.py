from django.urls import path
from . import views

app_name = "amazon_web"
urlpatterns = [
    path('', views.index, name='index'),
    path('register/',views.register,name='register'),
    path('login/', views.login, name='login'),
    path('dashboard/<int:id>/',views.dashboard, name='dashboard'),
    path('buyProduct/<int:id>/',views.buyProduct,name='buyProduct'),
    path('searchProduct/<int:id>/',views.searchProduct,name='searchProduct'),
    path('logout/', views.logout, name='logout'),
]