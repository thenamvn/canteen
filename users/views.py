from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, UpdateView, DetailView  # Thêm DetailView vào đây
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Address, SellerProfile
from .forms import UserRegisterForm, AddressForm, SellerProfileForm, UserLoginForm, ProfileUpdateForm
from django.contrib.auth.views import LoginView
from products.models import Product
from django.db.models import Avg, Count
from django.core.paginator import Paginator
from orders.models import OrderItem
from products.models import Product, Category
from django.urls import reverse_lazy, reverse
from django.contrib import messages
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
    
    def get_object(self):
        return self.request.user.seller_profile
        
    def get_success_url(self):
        return reverse_lazy('users:shop_profile', kwargs={'pk': self.object.pk})

@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thông tin của bạn đã được cập nhật thành công!')
            return redirect('users:profile')  # Adjust to your actual profile view name
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    return render(request, 'users/profile_edit.html', {'form': form})

class CustomLoginView(LoginView):
    form_class = UserLoginForm
    template_name = 'users/login.html'

# Thêm view sau class CustomLoginView
class ShopProfileView(DetailView):
    model = SellerProfile
    template_name = 'users/shop_profile.html'
    context_object_name = 'shop'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shop = self.get_object()
        
        # Lấy sản phẩm của shop
        products = Product.objects.filter(
            seller=shop.user,
            is_available=True
        ).order_by('-created_at')
        
        # Phân trang nếu cần
        paginator = Paginator(products, 12)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Lấy thống kê của shop
        stats = {
            'product_count': products.count(),
            'orders_count': OrderItem.objects.filter(product__seller=shop.user).values('order').distinct().count(),
        }
        
        # Sửa từ product thành products (số nhiều)
        context.update({
            'products': page_obj,
            'stats': stats,
            'categories': Category.objects.filter(products__seller=shop.user).distinct(),
        })
        return context
# Cập nhật SellerProfileUpdateView để chuyển hướng đến shop profile sau khi lưu
class SellerProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = SellerProfile
    form_class = SellerProfileForm
    template_name = 'users/seller_profile_form.html'
    
    def get_object(self):
        return self.request.user.seller_profile
        
    def get_success_url(self):
        return reverse_lazy('users:shop_profile', kwargs={'pk': self.object.pk})