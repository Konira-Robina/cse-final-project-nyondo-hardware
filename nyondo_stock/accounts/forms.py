from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import UserProfile
from validators import validate_ugandan_phone


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username',
            'autofocus': True,
        }),
        error_messages={
            'required': 'Username is required.',
        }
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password',
        }),
        error_messages={
            'required': 'Password is required.',
        }
    )

    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError(
                "This account is inactive. Contact the administrator.",
                code='inactive',
            )


class UserRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        error_messages={'required': 'Password is required.'}
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        error_messages={'required': 'Please confirm the password.'}
    )
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        error_messages={'required': 'Please select a role.'}
    )
    phone = forms.CharField(
        max_length=15,
        validators=[validate_ugandan_phone],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '0772123456'
        }),
        error_messages={'required': 'Phone number is required.'}
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
        error_messages = {
            'first_name': {'required': 'First name is required.'},
            'last_name': {'required': 'Last name is required.'},
            'username': {
                'required': 'Username is required.',
                'unique': 'This username is already taken.',
            },
        }

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name', '').strip()
        if not first_name:
            raise forms.ValidationError("First name is required.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name', '').strip()
        if not last_name:
            raise forms.ValidationError("Last name is required.")
        return last_name

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        if p1 and len(p1) < 8:
            raise forms.ValidationError(
                "Password must be at least 8 characters."
            )
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                role=self.cleaned_data['role'],
                phone=self.cleaned_data['phone'],
            )
        return user
class UserEditForm(forms.ModelForm):
        role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        error_messages={'required': 'Please select a role.'}
    )
        phone = forms.CharField(
        max_length=15,
        validators=[validate_ugandan_phone],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '0772123456'
        }),
        error_messages={'required': 'Phone number is required.'}
    )
        is_active = forms.BooleanField(
        required=False,
        label='Account Active',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
        class Meta:
             model = User
             fields = ['first_name', 'last_name', 'username', 'email', 'is_active']
             widgets = {
                  'first_name': forms.TextInput(attrs={'class': 'form-control'}),
                  'last_name': forms.TextInput(attrs={'class': 'form-control'}),
                  'username': forms.TextInput(attrs={'class': 'form-control'}),
                  'email': forms.EmailInput(attrs={'class': 'form-control'}),
                  }
        error_messages = {
            'first_name': {'required': 'First name is required.'},
            'last_name': {'required': 'Last name is required.'},
            'username': {
                'required': 'Username is required.',
                'unique': 'This username is already taken.',
            },
        }
        def __init__(self, *args, **kwargs):
             super().__init__(*args, **kwargs)
             if self.instance and hasattr(self.instance, 'profile'):
                  self.fields['role'].initial = self.instance.profile.role
                  self.fields['phone'].initial = self.instance.profile.phone
        def clean_first_name(self):
             name = self.cleaned_data.get('first_name', '').strip()
             if not name:
                  raise forms.ValidationError("First name is required.")
             return name

        def clean_last_name(self):
            name = self.cleaned_data.get('last_name', '').strip()
            if not name:
                 raise forms.ValidationError("Last name is required.")
            return name
        def save(self, commit=True):
             user = super().save(commit=commit)
             if commit:
                  profile = user.profile
                  profile.role = self.cleaned_data['role']
                  profile.phone = self.cleaned_data['phone']
                  profile.save()
                  return user