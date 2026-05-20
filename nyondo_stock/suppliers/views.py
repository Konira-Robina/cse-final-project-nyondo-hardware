from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import (
    Supplier, SupplierDelivery, SupplierDeliveryItem,
    SupplierCreditAccount, SupplierPayment
)
from .forms import (
    SupplierForm, SupplierDeliveryForm,
    SupplierDeliveryItemForm, SupplierPaymentForm
)
from stock.views import role_required


# ─── Supplier Views ────────────────────────────────────────────

@role_required(['store_manager', 'admin'])
def supplier_list(request):
    suppliers = Supplier.objects.all()
    form = SupplierForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, "Supplier registered.")
            return redirect('supplier_list')
    return render(request, 'suppliers/supplier_list.html', {
        'suppliers': suppliers,
        'form': form,
    })


@role_required(['store_manager', 'admin'])
def supplier_detail(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    deliveries = supplier.deliveries.all().order_by('-delivery_date')
    return render(request, 'suppliers/supplier_detail.html', {
        'supplier': supplier,
        'deliveries': deliveries,
    })


# ─── Delivery Views ────────────────────────────────────────────

@role_required(['store_manager', 'admin'])
def delivery_create(request):
    form = SupplierDeliveryForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            delivery = form.save(commit=False)
            delivery.recorded_by = request.user.get_full_name()
            delivery.save()
            messages.success(request, "Delivery recorded. Now add items.")
            return redirect('delivery_add_item', pk=delivery.pk)
    return render(request, 'suppliers/delivery_form.html', {'form': form})


@role_required(['store_manager', 'admin'])
def delivery_add_item(request, pk):
    delivery = get_object_or_404(SupplierDelivery, pk=pk)
    form = SupplierDeliveryItemForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            item = form.save(commit=False)
            item.delivery = delivery
            item.save()
            messages.success(request, "Item added to delivery.")

            # Check if user wants to add more or finish
            if 'add_more' in request.POST:
                return redirect('delivery_add_item', pk=delivery.pk)
            else:
                # If credit delivery, create credit account
                if delivery.is_credit:
                    SupplierCreditAccount.objects.get_or_create(
                        delivery=delivery,
                        defaults={
                            'total_amount': delivery.total_amount,
                        }
                    )
                messages.success(request, "Delivery completed and stock updated.")
                return redirect('delivery_detail', pk=delivery.pk)

    items = delivery.items.all()
    return render(request, 'suppliers/delivery_add_item.html', {
        'delivery': delivery,
        'form': form,
        'items': items,
    })


@role_required(['store_manager', 'admin'])
def delivery_detail(request, pk):
    delivery = get_object_or_404(SupplierDelivery, pk=pk)
    items = delivery.items.select_related('product').all()
    credit = getattr(delivery, 'credit_account', None)
    return render(request, 'suppliers/delivery_detail.html', {
        'delivery': delivery,
        'items': items,
        'credit': credit,
    })


@role_required(['store_manager', 'admin'])
def delivery_list(request):
    deliveries = SupplierDelivery.objects.select_related('supplier').order_by('-delivery_date')
    return render(request, 'suppliers/delivery_list.html', {'deliveries': deliveries})


# ─── Credit & Payment Views ────────────────────────────────────

@role_required(['admin'])
def credit_list(request):
    credits = SupplierCreditAccount.objects.select_related(
        'delivery__supplier'
    ).filter(is_cleared=False).order_by('due_date')
    cleared = SupplierCreditAccount.objects.filter(is_cleared=True).count()
    return render(request, 'suppliers/credit_list.html', {
        'credits': credits,
        'cleared': cleared,
    })


@role_required(['admin'])
def make_payment(request, pk):
    credit = get_object_or_404(SupplierCreditAccount, pk=pk)
    form = SupplierPaymentForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            amount = form.cleaned_data['amount']
            if amount > credit.balance_due:
                messages.error(
                    request,
                    f"Amount exceeds balance due of UGX {credit.balance_due:,.0f}."
                )
            else:
                payment = form.save(commit=False)
                payment.credit_account = credit
                payment.received_by = request.user.get_full_name()
                payment.save()
                messages.success(request, f"Payment of UGX {amount:,.0f} recorded.")
                return redirect('credit_list')

    return render(request, 'suppliers/make_payment.html', {
        'credit': credit,
        'form': form,
    })
