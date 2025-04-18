from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse_lazy
from .models import Product, Category
from .forms import ProductForm

# Helper function to check if user is a seller
def is_seller(user):
    return user.is_authenticated and user.is_seller

# Customer-facing views
class HomeView(ListView):
    model = Product
    template_name = 'products/home.html'
    context_object_name = 'products'
    paginate_by = 12
    ordering = '-created_at'
    
    def get_queryset(self):
        return Product.objects.filter(is_available=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(parent=None)
        return context

class CategoryProductsView(ListView):
    model = Product
    template_name = 'products/category_products.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'])
        return Product.objects.filter(category=self.category, is_available=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context

class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    slug_url_kwarg = 'slug'

# Seller Panel views
@login_required
@user_passes_test(is_seller)
def seller_dashboard(request):
    products = Product.objects.filter(seller=request.user)
    return render(request, 'products/seller/dashboard.html', {'products': products})

class SellerProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/seller/product_form.html'
    success_url = reverse_lazy('seller:dashboard')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_seller:
            return redirect('products:home')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.seller = self.request.user
        return super().form_valid(form)

class SellerProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/seller/product_form.html'
    success_url = reverse_lazy('seller:dashboard')
    
    def get_queryset(self):
        # Ensure sellers can only update their own products
        return Product.objects.filter(seller=self.request.user)
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_seller:
            return redirect('products:home')
        return super().dispatch(request, *args, **kwargs)

@login_required
@user_passes_test(is_seller)
def toggle_product_availability(request, pk):
    product = get_object_or_404(Product, pk=pk, seller=request.user)
    product.is_available = not product.is_available
    product.save()
    return redirect('seller:dashboard')

@login_required
@user_passes_test(is_seller)
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk, seller=request.user)
    if request.method == 'POST':
        product.delete()
    return redirect('seller:dashboard')