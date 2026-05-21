from django.contrib import admin
from .models import DepositCustomer, DepositRecord, GoodsPickup

# Register your models here.

class DepositRecordInline(admin.TabularInline):
    model = DepositRecord
    extra = 0
    fields = [
        'product', 'amount_paid',
        'receipt_number', 'payment_date'
    ]
    readonly_fields = ['receipt_number', 'payment_date']


class GoodsPickupInline(admin.TabularInline):
    model = GoodsPickup
    extra = 0
    fields = [
        'quantity_picked', 'amount_used',
        'served_by', 'pickup_date'
    ]
    readonly_fields = ['pickup_date']


@admin.register(DepositCustomer)
class DepositCustomerAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 'nin', 'phone',
        'employer', 'is_active',
        'total_deposited_display',
        'registration_date'
    ]
    list_filter = ['is_active', 'registration_date']
    search_fields = [
        'first_name', 'last_name',
        'nin', 'phone', 'employer'
    ]
    readonly_fields = ['registration_date']
    inlines = [DepositRecordInline]

    fieldsets = (
        ('Personal Information', {
            'fields': (
                'first_name', 'last_name',
                'nin', 'phone'
            )
        }),
        ('Additional Details', {
            'fields': ('employer', 'address')
        }),
        ('Account Status', {
            'fields': ('is_active', 'registration_date')
        }),
    )

    def total_deposited_display(self, obj):
        return f"UGX {obj.total_deposited():,.0f}"
    total_deposited_display.short_description = 'Total Deposited'


@admin.register(DepositRecord)
class DepositRecordAdmin(admin.ModelAdmin):
    list_display = [
        'receipt_number', 'customer',
        'product', 'amount_paid',
        'payment_date', 'has_pickup'
    ]
    list_filter = ['payment_date', 'product']
    search_fields = [
        'receipt_number',
        'customer__first_name',
        'customer__last_name',
        'customer__nin'
    ]
    readonly_fields = ['receipt_number', 'payment_date']
    inlines = [GoodsPickupInline]

    def has_pickup(self, obj):
        return obj.pickups.exists()
    has_pickup.boolean = True
    has_pickup.short_description = 'Picked Up'


@admin.register(GoodsPickup)
class GoodsPickupAdmin(admin.ModelAdmin):
    list_display = [
        'deposit', 'quantity_picked',
        'amount_used', 'served_by', 'pickup_date'
    ]
    list_filter = ['pickup_date']
    search_fields = [
        'deposit__customer__first_name',
        'deposit__customer__last_name',
        'served_by'
    ]
    readonly_fields = ['pickup_date']