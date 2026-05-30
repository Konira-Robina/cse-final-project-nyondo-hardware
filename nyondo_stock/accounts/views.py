from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required       
from django.contrib.auth import login, logout, authenticate 
from django.contrib import messages
from .forms import LoginForm, UserRegistrationForm
from .models import UserProfile
from sales.models import Sale
from stock.models import Product
from suppliers.models import SupplierCreditAccount
from deposits.models import DepositRecord
from django.db import models
from django.utils import timezone
from django.db.models import Sum

def index_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'index.html')
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.info(request, "You have been logged out successfully.")
        return redirect('index')
    return redirect('logout_confirm')
@login_required
def logout_confirm(request):
    return render(request, 'accounts/logout_confirm.html')


@login_required
def dashboard_view(request):
    today = timezone.now().date()

    total_products = Product.objects.count()
    low_stock = Product.objects.filter(
        quantity_in_stock__lte=models.F('low_stock_threshold')
    ).count()
    todays_sales = Sale.objects.filter(sale_date__date=today).count()
    
    # Calculate today's revenue
    todays_revenue = Sale.objects.filter(
        sale_date__date=today
    ).aggregate(
        total=models.Sum('grand_total')  
    )['total'] or 0

    pending_credits = SupplierCreditAccount.objects.filter(is_cleared=False).count()
    pending_deposits = DepositRecord.objects.filter(pickups__isnull=True).count()

    context = {
        'total_products': total_products,
        'low_stock': low_stock,
        'todays_sales': todays_sales,
        'todays_revenue': todays_revenue, 
        'pending_credits': pending_credits,
        'pending_deposits': pending_deposits,
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def register_user_view(request):
    # Only admin can register users
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'admin':
        messages.error(request, "You do not have permission to register users.")
        return redirect('dashboard')

    form = UserRegistrationForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, "User registered successfully.")
            return redirect('user_list')

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def user_list_view(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('dashboard')

    profiles = UserProfile.objects.select_related('user').all()
    return render(request, 'accounts/user_list.html', {'profiles': profiles})

from .forms import LoginForm, UserRegistrationForm, UserEditForm

@login_required
def user_edit(request, pk):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('dashboard')

    profile = get_object_or_404(UserProfile, pk=pk)
    form = UserEditForm(request.POST or None, instance=profile.user)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"{profile.user.get_full_name()} updated successfully."
            )
            return redirect('user_list')

    return render(request, 'accounts/user_edit.html', {
        'form': form,
        'profile': profile,
    })

@login_required
def user_delete(request, pk):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('dashboard')

    profile = get_object_or_404(UserProfile, pk=pk)
    if profile.user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('user_list')

    if request.method == 'POST':
        profile.user.delete()
        messages.success(request, "Staff account deleted.")
        return redirect('user_list')

    return render(request, 'accounts/user_confirm_delete.html', {
        'profile': profile,
    })
