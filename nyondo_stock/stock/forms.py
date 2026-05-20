from django import forms
from .models import Category, Product
from nyondo_stock.validators import validate_selling_price


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Cement, Iron Bars'
            })
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'category', 'name', 'description', 'unit',
            'unit_cost', 'wholesale_price', 'retailer_price',
            'retail_price', 'quantity_in_stock',
            'low_stock_threshold', 'is_deposit_eligible',
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3
            }),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'unit_cost': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': 'UGX'
            }),
            'wholesale_price': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': 'UGX'
            }),
            'retailer_price': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': 'UGX'
            }),
            'retail_price': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': 'UGX'
            }),
            'quantity_in_stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'low_stock_threshold': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_deposit_eligible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        cost = cleaned_data.get('unit_cost')
        wholesale = cleaned_data.get('wholesale_price')
        retailer = cleaned_data.get('retailer_price')
        retail = cleaned_data.get('retail_price')

        if all([cost, wholesale, retailer, retail]):
            errors = validate_selling_price(wholesale, retailer, retail, cost)
            for field, message in errors.items():
                self.add_error(field, message)

        return cleaned_data