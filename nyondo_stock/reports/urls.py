from django.urls import path
from . import views

urlpatterns = [
    path('sales/', views.sales_report, name='sales_report'),
    path('stock/', views.stock_report, name='stock_report'),
    path('credit/', views.credit_report, name='credit_report'),
    path('deposits/', views.deposit_report, name='deposit_report'),
]