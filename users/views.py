from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, UpdateView, DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import User, Address, SellerProfile
from .forms import UserRegisterForm, AddressForm, SellerProfileForm, UserLoginForm
from django.contrib.auth.views import LoginView

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # If user is registering as a seller, create an empty seller profile
            if user.is_seller:
                SellerProfile.objects.create(user=user, shop_name=f"{user.username}'s Shop")
            login(request, user)
            return redirect('products:home')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile(request):
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'users/profile.html', {'addresses': addresses})

class AddressCreateView(LoginRequiredMixin, CreateView):
    model = Address
    form_class = AddressForm
    template_name = 'users/address_form.html'
    success_url = reverse_lazy('users:profile')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class AddressUpdateView(LoginRequiredMixin, UpdateView):
    model = Address
    form_class = AddressForm
    template_name = 'users/address_form.html'
    success_url = reverse_lazy('users:profile')
    
    def get_queryset(self):
        # Ensure users can only update their own addresses
        return Address.objects.filter(user=self.request.user)

@login_required
def delete_address(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        address.delete()
    return redirect('users:profile')

class SellerProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = SellerProfile
    form_class = SellerProfileForm
    template_name = 'users/seller_profile_form.html'
    success_url = reverse_lazy('products:seller_dashboard')
    
    def get_object(self):
        return self.request.user.seller_profile

class CustomLoginView(LoginView):
    form_class = UserLoginForm
    template_name = 'users/login.html'