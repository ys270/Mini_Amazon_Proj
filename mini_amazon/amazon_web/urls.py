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
    path('query/<int:id>/',views.query,name='query'),
    path('query_one/<int:id>/',views.query_one,name='query_one'),
    path('rate/<int:id>/',views.rate,name='rate'),
    path('edit_profile/<int:id>/',views.edit_profile,name='edit_profile'),
    path('logout/', views.logout, name='logout'),
]