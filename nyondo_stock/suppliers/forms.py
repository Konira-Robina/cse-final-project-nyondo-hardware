from django import forms
from .models import (
    Supplier, SupplierDelivery,
    SupplierDeliveryItem, SupplierPayment
)
from validators import validate_ugandan_phone, validate_selling_price
from stock.models import Product, Category


class SupplierForm(forms.ModelForm):
    phone = forms.CharField(
        validators=[validate_ugandan_phone],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '0772123456'
        }),
        error_messages={
            'required': 'Phone number is required.',
        }
    )

    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'phone', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2
            }),
        }
        error_messages = {
            'name': {'required': 'Supplier name is required.'},
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError("Supplier name is required.")
        return name


class SupplierDeliveryForm(forms.ModelForm):
    class Meta:
        model = SupplierDelivery
        fields = ['supplier', 'delivery_date', 'payment_type', 'notes']
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'delivery_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'payment_type': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2
            }),
        }
        error_messages = {
            'supplier': {'required': 'Please select a supplier.'},
            'delivery_date': {'required': 'Delivery date is required.'},
            'payment_type': {'required': 'Please select a payment type.'},
        }


class SupplierDeliveryItemForm(forms.ModelForm):
    is_new_product = forms.BooleanField(
        required=False,
        label='This is a new product',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    new_product_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Product name'
        }),
        error_messages={'required': 'Product name is required.'}
    )
    new_product_category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        error_messages={'required': 'Category is required.'}
    )
    new_product_unit = forms.ChoiceField(
        choices=[('', '— Select unit —')] + Product.UNIT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        error_messages={'required': 'Unit is required.'}
    )
    new_product_is_deposit_eligible = forms.BooleanField(
        required=False,
        label='Eligible for deposit scheme',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = SupplierDeliveryItem
        fields = [
            'product', 'quantity', 'unit_cost',
            'wholesale_price', 'retailer_price', 'retail_price',
        ]
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 1
            }),
            'unit_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'UGX', 'min': 0
            }),
            'wholesale_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'UGX', 'min': 0
            }),
            'retailer_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'UGX', 'min': 0
            }),
            'retail_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'UGX', 'min': 0
            }),
        }
        error_messages = {
            'quantity': {
                'required': 'Quantity is required.',
                'invalid': 'Enter a valid number.',
            },
            'unit_cost': {'required': 'Unit cost is required.'},
            'wholesale_price': {'required': 'Wholesale price is required.'},
            'retailer_price': {'required': 'Retailer price is required.'},
            'retail_price': {'required': 'Retail price is required.'},
        }

    def clean(self):
        cleaned_data = super().clean()
        is_new = cleaned_data.get('is_new_product')

        if is_new:
            if not cleaned_data.get('new_product_name'):
                self.add_error('new_product_name', 'Product name is required.')
            if not cleaned_data.get('new_product_category'):
                self.add_error('new_product_category', 'Category is required.')
            if not cleaned_data.get('new_product_unit'):
                self.add_error('new_product_unit', 'Unit is required.')
        else:
            if not cleaned_data.get('product'):
                self.add_error('product', 'Please select a product.')

        cost = cleaned_data.get('unit_cost')
        wholesale = cleaned_data.get('wholesale_price')
        retailer = cleaned_data.get('retailer_price')
        retail = cleaned_data.get('retail_price')

        if all([cost, wholesale, retailer, retail]):
            errors = validate_selling_price(wholesale, retailer, retail, cost)
            for field, message in errors.items():
                self.add_error(field, message)

        return cleaned_data

    def save(self, commit=True):
        is_new = self.cleaned_data.get('is_new_product')
        if is_new:
            product = Product.objects.create(
                name=self.cleaned_data['new_product_name'],
                category=self.cleaned_data['new_product_category'],
                unit=self.cleaned_data['new_product_unit'],
                unit_cost=self.cleaned_data['unit_cost'],
                wholesale_price=self.cleaned_data['wholesale_price'],
                retailer_price=self.cleaned_data['retailer_price'],
                retail_price=self.cleaned_data['retail_price'],
                quantity_in_stock=0,
                is_deposit_eligible=self.cleaned_data.get(
                    'new_product_is_deposit_eligible', False
                ),
            )
            self.instance.product = product
        return super().save(commit=commit)


class SupplierPaymentForm(forms.ModelForm):
    class Meta:
        model = SupplierPayment
        fields = ['amount', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'UGX', 'min': 1
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2
            }),
        }
        error_messages = {
            'amount': {
                'required': 'Payment amount is required.',
                'invalid': 'Enter a valid amount.',
            }
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError(
                "Payment amount must be greater than zero."
            )
        return amount