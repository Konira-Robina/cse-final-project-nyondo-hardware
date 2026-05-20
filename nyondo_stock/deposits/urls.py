from django.urls import path
from . import views

urlpatterns = [
    path('', views.customer_list, name='customer_list'),
    path('register/', views.customer_register, name='customer_register'),
    path('<int:pk>/', views.customer_detail, name='customer_detail'),
    path('<int:customer_pk>/deposit/', views.deposit_record, name='deposit_record'),
    path('deposit/<int:pk>/receipt/', views.deposit_receipt, name='deposit_receipt'),
    path('deposit/<int:deposit_pk>/pickup/', views.goods_pickup, name='goods_pickup'),
]