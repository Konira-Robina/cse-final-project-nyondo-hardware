from django.contrib import admin
from .models import Cart, CartItem, Sale, SaleItem

# Register your models here.

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ['product', 'quantity']
    readonly_fields = []

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    fields = [
        'product', 'quantity',
        'unit_price', 'line_total'
    ]
    readonly_fields = ['unit_price', 'line_total']

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = [
        'attendant', 'customer_name', 'customer_type',
        'item_count', 'subtotal_display',
        'delivery_requested', 'updated_at'
    ]
    list_filter = ['customer_type', 'delivery_requested']
    search_fields = ['attendant__username', 'customer_name']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [CartItemInline]

    def subtotal_display(self, obj):
        return f"UGX {obj.subtotal:,.0f}"
    subtotal_display.short_description = 'Subtotal'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'quantity', 'line_total_display']
    search_fields = ['cart__attendant__username', 'product__name']

    def line_total_display(self, obj):
        return f"UGX {obj.line_total:,.0f}"
    line_total_display.short_description = 'Line Total'


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = [
        'receipt_number', 'customer_name',
        'customer_type', 'subtotal',
        'transport_status', 'grand_total',
        'served_by', 'sale_date'
    ]
    list_filter = [
        'customer_type', 'transport_status', 'sale_date'
    ]
    search_fields = [
        'receipt_number', 'customer_name',
        'customer_phone', 'served_by__username'
    ]
    readonly_fields = [
        'receipt_number', 'subtotal', 'transport_charge',
        'transport_status', 'grand_total', 'sale_date'
    ]
    inlines = [SaleItemInline]

    fieldsets = (
        ('Receipt', {
            'fields': ('receipt_number', 'sale_date', 'served_by')
        }),
        ('Customer', {
            'fields': (
                'customer_name', 'customer_phone', 'customer_type'
            )
        }),
        ('Delivery', {
            'fields': (
                'delivery_requested', 'within_10km',
                'transport_status', 'transport_charge'
            )
        }),
        ('Totals', {
            'fields': ('subtotal', 'grand_total')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )

@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = [
        'sale', 'product', 'quantity',
        'unit_price', 'line_total'
    ]
    search_fields = [
        'sale__receipt_number', 'product__name'
    ]
    readonly_fields = ['unit_price', 'line_total']