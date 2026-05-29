from django import forms
from .models import Category, Product
from validators import validate_selling_price


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Cement, Iron Bars',
            })
        }
        error_messages = {
            'name': {
                'required': 'Category name is required.',
                'unique': 'This category already exists.',
            }
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
                'class': 'form-control', 'placeholder': 'UGX', 'min': 0
            }),
            'wholesale_price': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': 'UGX', 'min': 0
            }),
            'retailer_price': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': 'UGX', 'min': 0
            }),
            'retail_price': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': 'UGX', 'min': 0
            }),
            'quantity_in_stock': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 0
            }),
            'low_stock_threshold': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 1
            }),
            'is_deposit_eligible': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        error_messages = {
            'name': {'required': 'Product name is required.'},
            'category': {'required': 'Please select a category.'},
            'unit': {'required': 'Please select a unit.'},
            'unit_cost': {
                'required': 'Unit cost is required.',
                'invalid': 'Enter a valid number.',
            },
            'wholesale_price': {
                'required': 'Wholesale price is required.',
            },
            'retailer_price': {
                'required': 'Retailer price is required.',
            },
            'retail_price': {
                'required': 'Retail price is required.',
            },
        }

    def clean_unit_cost(self):
        cost = self.cleaned_data.get('unit_cost')
        if cost is not None and cost <= 0:
            raise forms.ValidationError("Unit cost must be greater than zero.")
        return cost

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