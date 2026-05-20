from django.urls import path
from . import views

urlpatterns = [
    path('', views.supplier_list, name='supplier_list'),
    path('<int:pk>/', views.supplier_detail, name='supplier_detail'),
    path('deliveries/', views.delivery_list, name='delivery_list'),
    path('deliveries/new/', views.delivery_create, name='delivery_create'),
    path('deliveries/<int:pk>/', views.delivery_detail, name='delivery_detail'),
    path('deliveries/<int:pk>/add-item/', views.delivery_add_item, name='delivery_add_item'),
    path('credits/', views.credit_list, name='credit_list'),
    path('credits/<int:pk>/pay/', views.make_payment, name='make_payment'),
]