from django import forms
from .models import DepositCustomer, DepositRecord
from nyondo_stock.validators import validate_ugandan_phone, validate_nin


class DepositCustomerForm(forms.ModelForm):
    phone = forms.CharField(
        validators=[validate_ugandan_phone],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '0772123456'
        })
    )
    nin = forms.CharField(
        validators=[validate_nin],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'CM90001234ABCD'
        })
    )

    class Meta:
        model = DepositCustomer
        fields = [
            'first_name', 'last_name', 'nin',
            'phone', 'address', 'employer',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'employer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Employer / Organisation'
            }),
        }

    def clean_nin(self):
        nin = self.cleaned_data.get('nin', '').upper()
        # Check uniqueness manually to give a friendly message
        if DepositCustomer.objects.filter(nin=nin).exists():
            raise forms.ValidationError(
                "A customer with this NIN is already registered."
            )
        return nin


class DepositRecordForm(forms.ModelForm):
    class Meta:
        model = DepositRecord
        fields = ['product', 'amount_paid', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'amount_paid': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': 'UGX'
            }),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean_amount_paid(self):
        amount = self.cleaned_data.get('amount_paid')
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount