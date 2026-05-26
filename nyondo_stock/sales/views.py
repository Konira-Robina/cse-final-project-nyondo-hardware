from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Cart, CartItem, Sale, SaleItem
from .forms import CartCustomerForm, AddToCartForm, UpdateCartItemForm
from stock.models import Product
from notifications.utils import notify_new_sale, notify_low_stock
from django.core.paginator import Paginator
from django.db import models

def get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(attendant=user)
    return cart

@login_required
def cart_view(request):
    cart = get_or_create_cart(request.user)
    customer_form = CartCustomerForm(request.POST or None, instance=cart)
    add_form = AddToCartForm()

    if request.method == 'POST' and 'update_customer' in request.POST:
        if customer_form.is_valid():
            customer_form.save()
            messages.success(request, "Customer details updated.")
            return redirect('cart')

    return render(request, 'sales/cart.html', {
        'cart': cart,
        'customer_form': customer_form,
        'add_form': add_form,
    })


@login_required
def add_to_cart(request):
    if request.method == 'POST':
        cart = get_or_create_cart(request.user)
        form = AddToCartForm(request.POST)
        if form.is_valid():
            product = form.cleaned_data['product']
            quantity = form.cleaned_data['quantity']

            # Update or create cart item
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': quantity}
            )
            if not created:
                new_qty = cart_item.quantity + quantity
                if new_qty > product.quantity_in_stock:
                    messages.error(
                        request,
                        f"Cannot add more. Only {product.quantity_in_stock} "
                        f"{product.unit}(s) in stock."
                    )
                else:
                    cart_item.quantity = new_qty
                    cart_item.save()
                    messages.success(request, f"{product.name} quantity updated in cart.")
            else:
                messages.success(request, f"{product.name} added to cart.")
        else:
            for error in form.errors.values():
                messages.error(request, error)

    return redirect('cart')


@login_required
def remove_from_cart(request, pk):
    cart_item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
    if request.method == 'POST':
        cart_item.delete()
        messages.success(request, "Item removed from cart.")
    return redirect('cart')


@login_required
def update_cart_item(request, pk):
    
    cart_item = get_object_or_404(CartItem, pk=pk, cart__user=request.cart)
    if request.method == 'POST':
        form = UpdateCartItemForm(request.POST, cart_item=cart_item)
        if form.is_valid():
            cart_item.quantity = form.cleaned_data['quantity']
            cart_item.save()
            messages.success(request, "Quantity updated.")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    return redirect('cart')


@login_required
def checkout(request):
    cart = get_or_create_cart(request.user)

    if cart.is_empty():
        messages.error(request, "Your cart is empty.")
        return redirect('cart')

    if request.method == 'POST':
        # Create the Sale
        sale = Sale.objects.create(
            served_by=request.user,
            customer_name=cart.customer_name,
            customer_phone=cart.customer_phone,
            customer_type=cart.customer_type,
            delivery_requested=cart.delivery_requested,
            within_10km=cart.within_10km,
            subtotal=cart.subtotal,
        )

        # Create SaleItems and reduce stock
        for cart_item in cart.cart_items.select_related('product').all():
            SaleItem.objects.create(
                sale=sale,
                product=cart_item.product,
                quantity=cart_item.quantity,
            )
            # Reduce stock
            cart_item.product.quantity_in_stock -= cart_item.quantity
            cart_item.product.save()
            if cart_item.product.is_low_stock():
                notify_low_stock(cart_item.product)

        # Clear the cart
        cart.clear()

        messages.success(request, f"Sale completed! Receipt #{sale.receipt_number}")
        return redirect('receipt', pk=sale.pk)

    return render(request, 'sales/checkout.html', {'cart': cart})


@login_required
def receipt_view(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    items = sale.items.select_related('product').all()
    return render(request, 'sales/receipt.html', {
        'sale': sale,
        'items': items,
    })
@login_required
def receipt_print_view(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    items = sale.items.select_related('product').all()
    return render(request, 'sales/receipt_print.html', {
        'sale': sale,
        'items': items,
    })

@login_required

@login_required
def sales_list(request):
    search = request.GET.get('search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    customer_type = request.GET.get('customer_type', '')

    sales = Sale.objects.select_related('served_by').order_by('-sale_date')

    if search:
        sales = sales.filter(
            models.Q(receipt_number__icontains=search) |
            models.Q(customer_name__icontains=search) |
            models.Q(customer_phone__icontains=search)
        )

    if date_from:
        sales = sales.filter(sale_date__date__gte=date_from)

    if date_to:
        sales = sales.filter(sale_date__date__lte=date_to)

    if customer_type:
        sales = sales.filter(customer_type=customer_type)

    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(sales, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'sales/sales_list.html', {
        'sales': page_obj,
        'page_obj': page_obj,
        'search': search,
        'date_from': date_from,
        'date_to': date_to,
        'customer_type': customer_type,
        'customer_type_choices': Sale.CUSTOMER_TYPE_CHOICES,
        'total_count': sales.count(),
    })


