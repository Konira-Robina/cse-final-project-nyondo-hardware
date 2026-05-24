
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import DepositCustomer, DepositRecord, GoodsPickup
from .forms import DepositCustomerForm, DepositRecordForm
from stock.views import role_required
from django.db.models import Q
from notifications.utils import notify_new_deposit, notify_deposit_ready


@role_required(['admin', 'sales_attendant'])
@role_required(['admin', 'sales_attendant'])
def customer_list(request):
    search = request.GET.get('search', '')
    customers = DepositCustomer.objects.filter(is_active=True)

    if search:
        customers = customers.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(nin__icontains=search) |
            Q(phone__icontains=search) |
            Q(employer__icontains=search)
        )

    return render(request, 'deposits/customer_list.html', {
        'customers': customers,
        'search': search,
        'total_count': customers.count(),
    })


@role_required(['admin', 'sales_attendant'])
def customer_register(request):
    form = DepositCustomerForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, "Customer registered for deposit scheme.")
            return redirect('customer_list')
    return render(request, 'deposits/customer_form.html', {
        'form': form,
        'title': 'Register Deposit Customer',
    })


@role_required(['admin', 'sales_attendant'])
def customer_detail(request, pk):
    customer = get_object_or_404(DepositCustomer, pk=pk)
    deposits = customer.deposits.all().order_by('-payment_date')
    total_deposited = customer.total_deposited()
    return render(request, 'deposits/customer_detail.html', {
        'customer': customer,
        'deposits': deposits,
        'total_deposited': total_deposited,
    })


@role_required(['admin', 'sales_attendant'])
def deposit_record(request, customer_pk):
    customer = get_object_or_404(DepositCustomer, pk=customer_pk)
    form = DepositRecordForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            deposit = form.save(commit=False)
            deposit.customer = customer
            deposit.save()
            notify_new_deposit(deposit)
            notify_deposit_ready(deposit)
            messages.success(
                request,
                f"Deposit of UGX {deposit.amount_paid:,.0f} recorded. "
                f"Receipt #{deposit.receipt_number}"
            )
            return redirect('deposit_receipt', pk=deposit.pk)
    return render(request, 'deposits/deposit_form.html', {
        'form': form,
        'customer': customer,
    })


@role_required(['admin', 'sales_attendant'])
def deposit_receipt(request, pk):
    deposit = get_object_or_404(DepositRecord, pk=pk)
    return render(request, 'deposits/deposit_receipt.html', {'deposit': deposit})


@role_required(['admin', 'sales_attendant'])
def goods_pickup(request, deposit_pk):
    deposit = get_object_or_404(DepositRecord, pk=deposit_pk)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 0))
        amount_used = deposit.amount_paid

        if quantity <= 0:
            messages.error(request, "Quantity must be greater than zero.")
        elif quantity > deposit.product.quantity_in_stock:
            messages.error(
                request,
                f"Only {deposit.product.quantity_in_stock} "
                f"{deposit.product.unit}(s) in stock."
            )
        else:
            GoodsPickup.objects.create(
                deposit=deposit,
                quantity_picked=quantity,
                amount_used=amount_used,
                served_by=request.user.get_full_name(),
            )
            deposit.product.quantity_in_stock -= quantity
            deposit.product.save()
            messages.success(request, "Goods pickup recorded successfully.")
            return redirect('customer_detail', pk=deposit.customer.pk)

    return render(request, 'deposits/goods_pickup.html', {'deposit': deposit})

@role_required(['admin'])
def customer_edit(request, pk):
    customer = get_object_or_404(DepositCustomer, pk=pk)
    form = DepositCustomerForm(request.POST or None, instance=customer)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, "Customer details updated.")
            return redirect('customer_detail', pk=customer.pk)
    return render(request, 'deposits/customer_form.html', {
        'form': form,
        'title': f'Edit — {customer.full_name}',
    })


@role_required(['admin'])
def customer_deactivate(request, pk):
    customer = get_object_or_404(DepositCustomer, pk=pk)
    if request.method == 'POST':
        customer.is_active = not customer.is_active
        customer.save()
        status = "activated" if customer.is_active else "deactivated"
        messages.success(request, f"Customer {status}.")
        return redirect('customer_detail', pk=customer.pk)
    return render(request, 'deposits/customer_confirm_deactivate.html', {
        'customer': customer,
    })