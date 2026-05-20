from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Category, Product
from .forms import CategoryForm, ProductForm


def role_required(roles):
    """Decorator to restrict views by user role."""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not hasattr(request.user, 'profile'):
                messages.error(request, "Access denied.")
                return redirect('dashboard')
            if request.user.profile.role not in roles:
                messages.error(request, "You do not have permission for this action.")
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        wrapper.__name__ = view_func.__name__
        return login_required(wrapper)
    return decorator


# ─── Category Views ───────────────────────────────────────────

@role_required(['store_manager', 'admin'])
def category_list(request):
    categories = Category.objects.all()
    form = CategoryForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, "Category added.")
            return redirect('category_list')
    return render(request, 'stock/category_list.html', {
        'categories': categories,
        'form': form,
    })


@role_required(['store_manager', 'admin'])
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, "Category deleted.")
    return redirect('category_list')


# ─── Product Views ─────────────────────────────────────────────

@login_required
def product_list(request):
    products = Product.objects.select_related('category').all()
    low_stock = products.filter(quantity_in_stock__lte=models.F('low_stock_threshold'))
    return render(request, 'stock/product_list.html', {
        'products': products,
        'low_stock_count': low_stock.count(),
    })


@role_required(['store_manager', 'admin'])
def product_add(request):
    form = ProductForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, "Product registered successfully.")
            return redirect('product_list')
    return render(request, 'stock/product_form.html', {
        'form': form,
        'title': 'Register New Product',
    })


@role_required(['store_manager', 'admin'])
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, instance=product)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated.")
            return redirect('product_list')
    return render(request, 'stock/product_form.html', {
        'form': form,
        'title': f'Edit — {product.name}',
    })


@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'stock/product_detail.html', {'product': product})


@role_required(['store_manager', 'admin'])
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, "Product deleted.")
        return redirect('product_list')
    return render(request, 'stock/product_confirm_delete.html', {'product': product})


# fix missing import
from django.db import models
