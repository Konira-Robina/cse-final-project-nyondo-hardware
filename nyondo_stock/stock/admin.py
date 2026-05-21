from django.contrib import admin
from .models import Category, Product
# Register your models here.

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'product_count']
    search_fields = ['name']

    def product_count(self, obj):
        return obj.product_set.count()
    product_count.short_description = 'Products'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'unit',
        'unit_cost', 'wholesale_price', 'retailer_price',
        'retail_price', 'quantity_in_stock',
        'is_low_stock_display', 'is_deposit_eligible',
        'date_added',
    ]
    list_filter = ['category', 'unit', 'is_deposit_eligible']
    search_fields = ['name', 'description']
    readonly_fields = ['date_added']

    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'name', 'description', 'unit', 'is_deposit_eligible')
        }),
        ('Pricing (UGX)', {
            'fields': (
                'unit_cost', 'wholesale_price',
                'retailer_price', 'retail_price'
            ),
            'description': 'Rule: unit cost < wholesale < retailer < retail'
        }),
        ('Stock', {
            'fields': ('quantity_in_stock', 'low_stock_threshold')
        }),
        ('Metadata', {
            'fields': ('date_added',),
            'classes': ('collapse',)
        }),
    )

    def is_low_stock_display(self, obj):
        if obj.is_low_stock():
            return '⚠ Low'
        return '✓ OK'
    is_low_stock_display.short_description = 'Stock Status'