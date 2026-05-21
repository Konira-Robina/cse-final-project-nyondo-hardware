from django.contrib import admin
from .models import (Supplier, SupplierDelivery, SupplierDeliveryItem, SupplierCreditAccount, SupplierPayment)

# Register your models here.

class SupplierDeliveryItemInline(admin.TabularInline):
    model = SupplierDeliveryItem
    extra = 1
    fields = [
        'product', 'quantity', 'unit_cost',
        'wholesale_price', 'retailer_price',
        'retail_price', 'line_total'
    ]
    readonly_fields = ['line_total']


class SupplierPaymentInline(admin.TabularInline):
    model = SupplierPayment
    extra = 0
    fields = ['amount', 'payment_date', 'received_by', 'notes']
    readonly_fields = ['payment_date']


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'contact_person', 'phone',
        'delivery_count', 'date_added'
    ]
    search_fields = ['name', 'contact_person', 'phone']
    readonly_fields = ['date_added']

    def delivery_count(self, obj):
        return obj.deliveries.count()
    delivery_count.short_description = 'Deliveries'


@admin.register(SupplierDelivery)
class SupplierDeliveryAdmin(admin.ModelAdmin):
    list_display = [
        'supplier', 'delivery_date', 'payment_type',
        'total_amount_display', 'recorded_by'
    ]
    list_filter = ['payment_type', 'delivery_date']
    search_fields = ['supplier__name', 'notes']
    readonly_fields = ['recorded_by']
    inlines = [SupplierDeliveryItemInline]

    def total_amount_display(self, obj):
        return f"UGX {obj.total_amount:,.0f}"
    total_amount_display.short_description = 'Total Amount'


@admin.register(SupplierDeliveryItem)
class SupplierDeliveryItemAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'delivery', 'quantity',
        'unit_cost', 'line_total'
    ]
    search_fields = ['product__name', 'delivery__supplier__name']
    readonly_fields = ['line_total']


@admin.register(SupplierCreditAccount)
class SupplierCreditAccountAdmin(admin.ModelAdmin):
    list_display = [
        'delivery', 'total_amount', 'amount_paid',
        'balance_due_display', 'due_date', 'is_cleared'
    ]
    list_filter = ['is_cleared', 'due_date']
    search_fields = ['delivery__supplier__name']
    readonly_fields = ['is_cleared']
    inlines = [SupplierPaymentInline]

    def balance_due_display(self, obj):
        return f"UGX {obj.balance_due:,.0f}"
    balance_due_display.short_description = 'Balance Due'


@admin.register(SupplierPayment)
class SupplierPaymentAdmin(admin.ModelAdmin):
    list_display = [
        'credit_account', 'amount',
        'payment_date', 'received_by'
    ]
    list_filter = ['payment_date']
    search_fields = ['credit_account__delivery__supplier__name']
    readonly_fields = ['payment_date']