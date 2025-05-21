from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Address, SellerProfile

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    is_seller = forms.BooleanField(required=False, label="Register as a seller")
    
    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'is_seller', 'password1', 'password2']


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label='Username or Email')
    
    class Meta:
        model = User
        fields = ['username', 'password']


class SellerProfileForm(forms.ModelForm):
    class Meta:
        model = SellerProfile
        fields = ['shop_name', 'shop_description', 'shop_logo']


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['recipient_name', 'phone_number', 'street_address', 'ward', 'district', 'city', 'is_default']
        
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number']  # Updated to match your model fields
        
        # Widgets for better form appearance with tailwind classes instead of bootstrap
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-orange-500 focus:ring-orange-500'}),
            'last_name': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-orange-500 focus:ring-orange-500'}),
            'phone_number': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-orange-500 focus:ring-orange-500'}),
        }