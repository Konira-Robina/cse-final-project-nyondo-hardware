from django.urls import path
from . import views

urlpatterns = [
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:pk>/', views.update_cart_item, name='update_cart_item'),
    path('cart/checkout/', views.checkout, name='checkout'),
    path('receipt/<int:pk>/', views.receipt_view, name='receipt'),
    path('', views.sales_list, name='sales_list'),
    path('receipt/<int:pk>/print/', views.receipt_print_view, name='receipt_print'),
]